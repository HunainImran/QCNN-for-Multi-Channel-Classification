# import packages
import tensorflow as tf
import tensorflow_quantum as tfq
from tensorflow.keras import layers
import cirq
import sympy
import numpy as np
from utils import normalize_tensor_by_index

#######################
# define a keras layer class to contain the quantum convolutional layer
class U1_circuit(tf.keras.layers.Layer):

    # initialize class
    def __init__(self, n_kernels, n_input_channels, datatype, registers=1, rdpa=1, inter_U=False, activation=None, name=None, kernel_regularizer=None, **kwargs):
        super(U1_circuit, self).__init__(name=name, **kwargs)
        self.n_kernels = n_kernels
        self.n_input_channels = n_input_channels
        self.registers = registers
        self.rdpa = rdpa
        self.ancilla = int(registers/rdpa)
        self.datatype = datatype
        self.inter_U = inter_U
        self.learning_params = []
        self.Q_circuit()
        self.activation = tf.keras.layers.Activation(activation)
        self.kernel_regularizer = kernel_regularizer

    # define function to return a new learnable parameter, save all parameters
    def get_new_param(self):

        # generate symbol for parameter
        new_param = sympy.symbols("p"+str(len(self.learning_params)))

        # append new parameter to learning_params
        self.learning_params.append(new_param)

        # return the parameter
        return new_param



    # define quantum circuit
    def Q_circuit(self):
        # define number of pixels
        n_pixels = self.n_input_channels*(2**2)
        circuit_layers = -(-self.n_input_channels//self.registers)
        qubit_registers = [cirq.GridQubit.rect(1, self.ancilla, top=0)]
        for i in range(self.registers):
          qubit_registers.append(cirq.GridQubit.rect(1, 2**2, top=i+1))


        # initialize qubits in circuit

        input_params = [sympy.symbols('a%d' %i) for i in range(n_pixels)]
        # intitialize circuit
        self.circuit = cirq.Circuit()

        # define function to entangle the inputs with a gate that applies a controlled
        # power of a CX gate
        def Q_new_entangle(self, source, target, qubits_tar, qubits_src):
          yield cirq.CXPowGate(exponent=self.get_new_param())(qubits_tar[target], qubits_src[source])

        # angle encodes the input data
        def Q_embed(self,layer_index, register_index,qubits):
          starting_parameter = (2**2)*(register_index+(layer_index*self.registers))
          
          for i in range(len(qubits)):
            self.circuit.append(cirq.rx(np.pi*input_params[starting_parameter+i])(qubits[i]))         
        
        # strongly entangles the data with each channel
        def Q_entangle_intra_data(self,qubits):
          self.circuit.append(Q_new_entangle(self,1, 0, qubits, qubits))
          self.circuit.append(Q_new_entangle(self,2, 1, qubits, qubits))
          self.circuit.append(Q_new_entangle(self,3, 2, qubits, qubits))
          self.circuit.append(Q_new_entangle(self,0, 3, qubits, qubits))

        # strongly entangles all channels
        def Q_entangle_inter_data(self,qubits_all):
          if self.registers > 2:
            for i in range(1,len(qubits_all),1):
              if i != len(qubits_all) - 1:
                self.circuit.append(Q_new_entangle(self,0, 0, qubits_all[i+1], qubits_all[i]))
              else:
                self.circuit.append(Q_new_entangle(self,0, 0, qubits_all[1], qubits_all[i]))

          else:
            self.circuit.append(Q_new_entangle(self,0, 0, qubits_all[1], qubits_all[2]))

        # deposits quantum phase onto the ancilla
        def Q_deposit(self,qubits,ancilla):
          self.circuit.append(cirq.CZPowGate(exponent=self.get_new_param())(qubits[0], qubit_registers[0][ancilla]))

        # entangle the ancilla qubits if applicable
        def Q_ancilla_entangle(self,qubits):
          if self.ancilla > 2:
            for i in range(self.ancilla):
              if i != self.ancilla - 1:
                  self.circuit.append(Q_new_entangle(self,i, i+1, qubits, qubits))
              else:
                  self.circuit.append(Q_new_entangle(self,0, i, qubits, qubits))
          else:
            self.circuit.append(Q_new_entangle(self,0, 1, qubits, qubits))

        # Begin to build quantum circuit
        
        # append hadamard gates to all ancilla wires
        for i in range(self.ancilla):
           self.circuit.append(cirq.H(qubit_registers[0][i]))
           
        for j in range(circuit_layers):
            
          # angle encode classical data
          for i in range(self.registers):
            Q_embed(self,j,i,qubit_registers[i+1])

          # entangle data within each channel
          for i in range(self.registers):
            Q_entangle_intra_data(self,qubit_registers[i+1])

          # entangle data between each channel
          if self.registers > 1 and self.inter_U:
            Q_entangle_inter_data(self,qubit_registers)

          # exchange phase from all working registers to the ancilla
          ancilla_count = 1
          for i in range(self.registers):
            Q_deposit(self,qubit_registers[i+1],ancilla_count-1)
            if ancilla_count < self.ancilla:
              ancilla_count = ancilla_count + 1

          # entangle the ancilla qubits
          if self.registers > 1 and self.ancilla > 1:
            Q_ancilla_entangle(self,qubit_registers[0])
        
        print("Circuit Depth: "+str(len(cirq.Circuit(self.circuit.all_operations()))))

        # create list of embedding and learnable parameters
        self.params = input_params + self.learning_params

        # perform measurements on first qubit
        self.measurement = cirq.X(qubit_registers[0][0])
    
    # define keras backend function for initializing kernel
    def build(self, input_shape):

        self.width = input_shape[1]
        self.height = input_shape[2]

        self.num_x = self.width - 2 + 1
        self.num_y = self.height - 2 + 1

        # initialize kernel of shape(n_kernels, n_input_learnable_params)
        self.kernel = self.add_weight(name="kernel",
                                      shape=[self.n_kernels, 1, len(self.learning_params)],
                                      initializer=tf.keras.initializers.glorot_normal(seed=42),
                                      regularizer=self.kernel_regularizer)

        # create circuit tensor containing values for each convolution step
        self.circuit_tensor = tfq.convert_to_tensor([self.circuit] * self.num_x * self.num_y)
    # define a function to return a tensor of expectation values for each stride
    def get_expectations(self, input_data, controller, circuit_batch):


        input_data = tf.concat([input_data, controller], 1)

        # get expectation value for each data point for each batch for a kernel
        output = tfq.layers.Expectation()(circuit_batch,
                                               symbol_names=self.params,
                                               symbol_values=input_data,
                                               operators=self.measurement)

        output = tf.reshape(output, shape=[-1, self.num_x, self.num_y])
        return output
    # define keras backend function to stride kernel and collect data
    def call(self, inputs):
        
        
        inputs = normalize_tensor_by_index(inputs,self.datatype)   
        

        stack_set = None

        # stride and collect data from input image
        for i in range(self.num_x):
            for j in range(self.num_y):

                # collecting image data superimposed with kernel

                slice_part = tf.slice(inputs, [0, i, j, 0], [-1, 2, 2, -1])

                # reshape to [batch_size, n_strides, filter_size, filter_size, n_input_channels]
                slice_part = tf.reshape(slice_part, shape=[-1, 1, 2, 2, self.n_input_channels])

                # if this is first stride, define new variable
                if stack_set == None:
                    stack_set = slice_part

                # if not first stride, concatenate to data from past strides
                else:
                    stack_set = tf.concat([stack_set, slice_part], 1)

        # permute shape to [batch_size, n_strides,  n_input_channels, filter_size, filter_size]
        stack_set = tf.transpose(stack_set, perm=[0, 1, 4, 2, 3])

        # reshape to [batch_size*n_strides,n_input_channels*filter_size*filter_size]

        stack_set = tf.reshape(stack_set, shape=[-1, self.n_input_channels*(2**2)])

        # create new tensor by tiling circuit values for each data point in batch
        circuit_batch = tf.tile([self.circuit_tensor], [tf.shape(inputs)[0], 1])

        # flatten circuit tensor
        circuit_batch = tf.reshape(circuit_batch, shape=[-1])

        # initialize list to hold expectation values
        outputs = []
        for i in range(self.n_kernels):

            # create new tensor by tiling kernel values for each stride for each

            controller = tf.tile(self.kernel[i], [tf.shape(inputs)[0]*self.num_x*self.num_y, 1])

            # append to a list the expectations for all input data in the batch,

            outputs.append(self.get_expectations(stack_set, controller, circuit_batch))

        # stack the expectation values for each kernel

        output_tensor = tf.stack(outputs, axis=3)

        # if values are less than -1 or greater than 1, make -1 or 1, respectively
        output_tensor = tf.math.acos(tf.clip_by_value(output_tensor, -1+1e-5, 1-1e-5)) / np.pi

        # return the activated tensor of expectation values
        return self.activation(output_tensor)

####U1 MODIFIED CIRCUIT WITH MORE PHASE ENTANGLEMENT BETWEEN THE ANCILLARY QUBIT AND THE THE REST OF THE PIXEL QUBITS####
class U1_Modified_circuit(tf.keras.layers.Layer):

    # initialize class
    def __init__(self, n_kernels, n_input_channels, datatype, registers=1, rdpa=1, inter_U=False, activation=None, name=None, kernel_regularizer=None, **kwargs):
        super(U1_Modified_circuit, self).__init__(name=name, **kwargs)
        self.n_kernels = n_kernels
        self.n_input_channels = n_input_channels
        self.registers = registers
        self.rdpa = rdpa
        self.ancilla = int(registers/rdpa)
        self.datatype = datatype
        self.inter_U = inter_U
        self.learning_params = []
        self.Q_circuit()
        self.activation = tf.keras.layers.Activation(activation)
        self.kernel_regularizer = kernel_regularizer

    # define function to return a new learnable parameter, save all parameters
    # in self.learning_params
    def get_new_param(self):

        # generate symbol for parameter
        new_param = sympy.symbols("p"+str(len(self.learning_params)))

        # append new parameter to learning_params
        self.learning_params.append(new_param)

        # return the parameter
        return new_param



    # define quantum circuit
    def Q_circuit(self):
        # define number of pixels
        n_pixels = self.n_input_channels*(2**2)
        circuit_layers = -(-self.n_input_channels//self.registers)
        qubit_registers = [cirq.GridQubit.rect(1, self.ancilla, top=0)]
        for i in range(self.registers):
          qubit_registers.append(cirq.GridQubit.rect(1, 2**2, top=i+1))


        # initialize qubits in circuit

        input_params = [sympy.symbols('a%d' %i) for i in range(n_pixels)]
        # intitialize circuit
        self.circuit = cirq.Circuit()

        # define function to entangle the inputs with a gate that applies a controlled
        # power of a CX gate
        def Q_new_entangle(self, source, target, qubits_tar, qubits_src):
          yield cirq.CXPowGate(exponent=self.get_new_param())(qubits_tar[target], qubits_src[source])

        # angle encodes the input data
        def Q_embed(self,layer_index, register_index,qubits):
          starting_parameter = (2**2)*(register_index+(layer_index*self.registers))
          
          for i in range(len(qubits)):
            self.circuit.append(cirq.rx(np.pi*input_params[starting_parameter+i])(qubits[i]))         
        
        # strongly entangles the data with each channel
        def Q_entangle_intra_data(self,qubits):
          self.circuit.append(Q_new_entangle(self,1, 0, qubits, qubits))
          self.circuit.append(Q_new_entangle(self,2, 1, qubits, qubits))
          self.circuit.append(Q_new_entangle(self,3, 2, qubits, qubits))
          self.circuit.append(Q_new_entangle(self,0, 3, qubits, qubits))

        # strongly entangles all channels
        def Q_entangle_inter_data(self,qubits_all):
          if self.registers > 2:
            for i in range(1,len(qubits_all),1):
              if i != len(qubits_all) - 1:
                self.circuit.append(Q_new_entangle(self,0, 0, qubits_all[i+1], qubits_all[i]))
              else:
                self.circuit.append(Q_new_entangle(self,0, 0, qubits_all[1], qubits_all[i]))

          else:
            self.circuit.append(Q_new_entangle(self,0, 0, qubits_all[1], qubits_all[2]))

        # deposits quantum phase onto the ancilla
        def Q_deposit(self,qubits,ancilla):
          # entangle all the working qubits with the ancilla
          self.circuit.append(cirq.CZPowGate(exponent=self.get_new_param())(qubits[0], qubit_registers[0][ancilla]))
          self.circuit.append(cirq.CZPowGate(exponent=self.get_new_param())(qubits[1], qubit_registers[0][ancilla]))
          self.circuit.append(cirq.CZPowGate(exponent=self.get_new_param())(qubits[2], qubit_registers[0][ancilla]))
          self.circuit.append(cirq.CZPowGate(exponent=self.get_new_param())(qubits[3], qubit_registers[0][ancilla]))

        # entangle the ancilla qubits if applicable
        def Q_ancilla_entangle(self,qubits):
          if self.ancilla > 2:
            for i in range(self.ancilla):
              if i != self.ancilla - 1:
                  self.circuit.append(Q_new_entangle(self,i, i+1, qubits, qubits))
              else:
                  self.circuit.append(Q_new_entangle(self,0, i, qubits, qubits))
          else:
            self.circuit.append(Q_new_entangle(self,0, 1, qubits, qubits))

        # Begin to build quantum circuit
        
        # append hadamard gates to all ancilla wires
        for i in range(self.ancilla):
           self.circuit.append(cirq.H(qubit_registers[0][i]))
           
        for j in range(circuit_layers):
            
          # angle encode classical data
          for i in range(self.registers):
            Q_embed(self,j,i,qubit_registers[i+1])

          # entangle data within each channel
          for i in range(self.registers):
            Q_entangle_intra_data(self,qubit_registers[i+1])

          # entangle data between each channel
          if self.registers > 1 and self.inter_U:
            Q_entangle_inter_data(self,qubit_registers)

          # exchange phase from all working registers to the ancilla
          ancilla_count = 1
          for i in range(self.registers):
            Q_deposit(self,qubit_registers[i+1],ancilla_count-1)
            if ancilla_count < self.ancilla:
              ancilla_count = ancilla_count + 1

          # entangle the ancilla qubits
          if self.registers > 1 and self.ancilla > 1:
            Q_ancilla_entangle(self,qubit_registers[0])
        
        print("Circuit Depth: "+str(len(cirq.Circuit(self.circuit.all_operations()))))

        # create list of embedding and learnable parameters
        self.params = input_params + self.learning_params

        # perform measurements on first qubit
        self.measurement = cirq.X(qubit_registers[0][0])
    
    # define keras backend function for initializing kernel
    def build(self, input_shape):

        self.width = input_shape[1]
        self.height = input_shape[2]

        self.num_x = self.width - 2 + 1
        self.num_y = self.height - 2 + 1

        # initialize kernel of shape(n_kernels, n_input_learnable_params)
        self.kernel = self.add_weight(name="kernel",
                                      shape=[self.n_kernels, 1, len(self.learning_params)],
                                      initializer=tf.keras.initializers.glorot_normal(seed=42),
                                      regularizer=self.kernel_regularizer)

        # create circuit tensor containing values for each convolution step
        self.circuit_tensor = tfq.convert_to_tensor([self.circuit] * self.num_x * self.num_y)
    # define a function to return a tensor of expectation values for each stride
    def get_expectations(self, input_data, controller, circuit_batch):

        input_data = tf.concat([input_data, controller], 1)

        # get expectation value for each data point for each batch for a kernel
        output = tfq.layers.Expectation()(circuit_batch,
                                               symbol_names=self.params,
                                               symbol_values=input_data,
                                               operators=self.measurement)

        output = tf.reshape(output, shape=[-1, self.num_x, self.num_y])
        return output
    # define keras backend function to stride kernel and collect data
    def call(self, inputs):
        
        
        inputs = normalize_tensor_by_index(inputs,self.datatype)   
        
        # define dummy variable to check if we are collecting data for first step
        stack_set = None

        # stride and collect data from input image
        for i in range(self.num_x):
            for j in range(self.num_y):

                # collecting image data superimposed with kernel
                slice_part = tf.slice(inputs, [0, i, j, 0], [-1, 2, 2, -1])

                # reshape to [batch_size, n_strides, filter_size, filter_size, n_input_channels]
                slice_part = tf.reshape(slice_part, shape=[-1, 1, 2, 2, self.n_input_channels])

                if stack_set == None:
                    stack_set = slice_part

                # if not first stride, concatenate to data from past strides
                else:
                    stack_set = tf.concat([stack_set, slice_part], 1)

        # permute shape to [batch_size, n_strides,  n_input_channels, filter_size, filter_size]
        stack_set = tf.transpose(stack_set, perm=[0, 1, 4, 2, 3])

        # reshape to [batch_size*n_strides,n_input_channels*filter_size*filter_size]
        stack_set = tf.reshape(stack_set, shape=[-1, self.n_input_channels*(2**2)])

        # create new tensor by tiling circuit values for each data point in batch
        circuit_batch = tf.tile([self.circuit_tensor], [tf.shape(inputs)[0], 1])

        # flatten circuit tensor
        circuit_batch = tf.reshape(circuit_batch, shape=[-1])

        # initialize list to hold expectation values
        outputs = []
        for i in range(self.n_kernels):

            controller = tf.tile(self.kernel[i], [tf.shape(inputs)[0]*self.num_x*self.num_y, 1])

            outputs.append(self.get_expectations(stack_set, controller, circuit_batch))

        # stack the expectation values for each kernel
        output_tensor = tf.stack(outputs, axis=3)
        # if values are less than -1 or greater than 1, make -1 or 1, respectively
        output_tensor = tf.math.acos(tf.clip_by_value(output_tensor, -1+1e-5, 1-1e-5)) / np.pi

        # return the activated tensor of expectation values
        return self.activation(output_tensor)

class Q_U1_control(tf.keras.layers.Layer):

    # initialize class
    def __init__(self, n_kernels, datatype, padding=False, classical_weights=False, activation=None, name=None, kernel_regularizer=None, **kwargs):
        super(Q_U1_control, self).__init__(name=name, **kwargs)
        self.n_kernels = n_kernels
        self.classical_weights = classical_weights
        self.datatype = datatype
        self.learning_params = []
        self.Q_circuit()
        self.activation = tf.keras.layers.Activation(activation)
        self.kernel_regularizer = kernel_regularizer

    # define function to return a new learnable parameter, save all parameters
    # in self.learning_params
    def get_new_param(self):

        # generate symbol for parameter
        new_param = sympy.symbols("p"+str(len(self.learning_params)))

        # append new parameter to learning_params
        self.learning_params.append(new_param)

        # return the parameter
        return new_param

    # define function to entangle the inputs with a gate that applies a controlled
    # power of an X gate
    def Q_entangle(self, source, target, qubits):
        yield cirq.CXPowGate(exponent=self.get_new_param())(qubits[source], qubits[target])

    # define quantum circuit
    def Q_circuit(self):
        # define number of pixels
        n_pixels = 2**2

        # initialize qubits in circuit
        cirq_qubits = cirq.GridQubit.rect(n_pixels,1)

        # intitialize circuit
        self.circuit = cirq.Circuit()

        input_params = [sympy.symbols('a%d' %i) for i in range(n_pixels)]

        for i, qubit in enumerate(cirq_qubits):
            self.circuit.append(cirq.rx(np.pi*input_params[i])(qubit))

        # ENTANGLE: strongly entangle all qubits
        for i in range(n_pixels):
            if i != n_pixels - 1:
              self.circuit.append(self.Q_entangle(i, i+1, cirq_qubits))
            else:
              self.circuit.append(self.Q_entangle(0, i, cirq_qubits))
              
        print("Circuit Depth: "+str(len(cirq.Circuit(self.circuit.all_operations()))))

        # create list of embedding and learnable parameters
        self.params = input_params + self.learning_params

        # perform measurements on first qubit
        
        self.measurement = cirq.Z(cirq_qubits[0])
        
        # define keras backend function for initializing kernel
    def build(self, input_shape):

        self.width = input_shape[1]
        self.height = input_shape[2]
        self.n_input_channels = input_shape[3]

        # define output dimensions for stride 1 with padding 1

        self.num_x = self.width - 2 + 1
        self.num_y = self.height - 2 + 1

        # initialize kernel of shape(n_kernels, n_input_channels, n_input_learnable_params
        self.kernel = self.add_weight(name="kernel",
                                      shape=[self.n_kernels, self.n_input_channels, len(self.learning_params)],
                                      initializer=tf.keras.initializers.glorot_normal(seed=42),
                                      regularizer=self.kernel_regularizer)

        if self.classical_weights:
            self.channel_weights = self.add_weight(name="channel_w",
                                          shape=[self.num_x,self.num_y,self.n_input_channels],
                                          initializer=tf.keras.initializers.RandomNormal(mean=1.0,stddev=0.1,seed=42),
                                          regularizer=self.kernel_regularizer)
        
            self.channel_bias = self.add_weight(name="channel_b",
                                          shape=[self.num_x,self.num_y,self.n_input_channels],
                                          initializer=tf.keras.initializers.RandomNormal(mean=0.0,stddev=0.1,seed=42),
                                          regularizer=self.kernel_regularizer)



        # create circuit tensor containing values for each convolution step
        self.circuit_tensor = tfq.convert_to_tensor([self.circuit] * self.num_x * self.num_y * self.n_input_channels)

    # define a function to return a tensor of expectation values for each stride
    def get_expectations(self, input_data, controller, circuit_batch):

        input_data = tf.concat([input_data, controller], 1)

        # get expectation value for each data point for each batch for a kernel
        output = tfq.layers.Expectation()(circuit_batch,
                                               symbol_names=self.params,
                                               symbol_values=input_data,
                                               operators=self.measurement)
        # reshape tensor of expectation value
        output = tf.reshape(output, shape=[-1, self.num_x, self.num_y, self.n_input_channels])
        if self.classical_weights:
            output = tf.math.multiply(output,self.channel_weights)
            output = tf.math.add(output,self.channel_bias)
        return tf.math.reduce_sum(output, 3)
    def call(self, inputs):
        
        if self.classical_weights:
            inputs = normalize_tensor_by_index(inputs,self.datatype)
        # define dummy variable to check if we are collecting data for first step
        stack_set = None

        # stride and collect data from input image
        for i in range(self.num_x):
            for j in range(self.num_y):

                slice_part = tf.slice(inputs, [0, i, j, 0], [-1, 2, 2, -1])

                # reshape to [batch_size, n_strides, filter_size, filter_size, n_input_channels]
                slice_part = tf.reshape(slice_part, shape=[-1, 1, 2, 2, self.n_input_channels])

                if stack_set == None:
                    stack_set = slice_part

                # if not first stride, concatenate to data from past strides
                else:
                    stack_set = tf.concat([stack_set, slice_part], 1)

        # permute shape to [batch_size, n_strides,  n_input_channels, filter_size, filter_size]
        stack_set = tf.transpose(stack_set, perm=[0, 1, 4, 2, 3])

        # reshape to [batch_size*n_strides*n_input_channels, filter_size*filter_size]
        stack_set = tf.reshape(stack_set, shape=[-1, 2**2])

        circuit_batch = tf.tile([self.circuit_tensor], [tf.shape(inputs)[0], 1])

        # flatten circuit tensor
        circuit_batch = tf.reshape(circuit_batch, shape=[-1])


        # initialize list to hold expectation values
        outputs = []
        for i in range(self.n_kernels):

            controller = tf.tile(self.kernel[i], [tf.shape(inputs)[0]*self.num_x*self.num_y, 1])

            # append to a list the expectations for all input data in the batch
            outputs.append(self.get_expectations(stack_set, controller, circuit_batch))

        # stack the expectation values for each kernel
        output_tensor = tf.stack(outputs, axis=3)
        # if values are less than -1 or greater than 1, make -1 or 1, respectively
        output_tensor = tf.math.acos(tf.clip_by_value(output_tensor, -1+1e-5, 1-1e-5)) / np.pi

        # return the activated tensor of expectation values
        return self.activation(output_tensor)
