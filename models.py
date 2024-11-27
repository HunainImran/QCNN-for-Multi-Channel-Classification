# import packages
import tensorflow as tf
import matplotlib.pyplot as plt
import cirq
from cirq.contrib.svg import circuit_to_svg
from tensorflow.keras import datasets, layers, models

from circuits import U1_circuit, Q_U1_control, U1_Modified_circuit
# , U2_circuit, Q_U2_control 

###########################
# build quantum convolutional neural network
def CO_U1_QCNN_model(datatype,classes):
# conditionally set input layer and quantum layer depending on the dataset
    def plot_circuit(circuit, save_path="circuit_diagram.svg"):
        """
        Visualizes and saves a quantum circuit as an SVG file.
        """
        # Generate the SVG representation
        svg = circuit_to_svg(circuit)

        # Save to an SVG file
        with open(save_path, "w") as f:
            f.write(svg)
            print(f"Circuit diagram saved to: {save_path}")

    if datatype == "CHANNELS":
        x_input = tf.keras.layers.Input((10,10,12), name = 'input')

        x_qconv1 = U1_circuit(n_kernels=3, n_input_channels=12,activation='relu', datatype=datatype,
                      name='CO_U1_QCNN')(x_input)

    if datatype == "COLORS" or datatype == "CIFAR10" or datatype == "COLORS_SHAPE":
        x_input = tf.keras.layers.Input((10,10,3), name = 'input')

        # Create an instance of U1_circuit
        u1_circuit_layer = U1_circuit(n_kernels=3, n_input_channels=3, activation='relu',
                                      datatype=datatype, name='CO_U1_QCNN')

        # Print the circuit before applying the layer to the input
        print("Quantum Circuit:")
        print(u1_circuit_layer.circuit.to_text_diagram())
        plot_circuit(u1_circuit_layer.circuit)

        # Apply the circuit layer
        x_qconv1 = u1_circuit_layer(x_input)


    x_flatten = tf.keras.layers.Flatten()(x_qconv1)

    x_fc1 = tf.keras.layers.Dense(32, activation='relu')(x_flatten)

    if datatype == "COLORS":
        x_fc2 = tf.keras.layers.Dense(9, activation='softmax')(x_fc1)
    
    elif datatype == "COLORS_SHAPE":
        x_fc2 = tf.keras.layers.Dense(24, activation='softmax')(x_fc1)
    
    else:
        x_fc2 = tf.keras.layers.Dense(classes, activation='softmax')(x_fc1)

    return tf.keras.models.Model(inputs = x_input, outputs = x_fc2, name = 'CO_U1_QCNN')

###########################
# build quantum convolutional neural network
def MODIFIED_CO_U1_QCNN_model(datatype,classes):
# conditionally set input layer and quantum layer depending on the dataset
    def plot_circuit(circuit, save_path="circuit_diagram.svg"):
        """
        Visualizes and saves a quantum circuit as an SVG file.
        """
        # Generate the SVG representation
        svg = circuit_to_svg(circuit)

        # Save to an SVG file
        with open(save_path, "w") as f:
            f.write(svg)
            print(f"Circuit diagram saved to: {save_path}")

    if datatype == "CHANNELS":
        x_input = tf.keras.layers.Input((10,10,12), name = 'input')

        x_qconv1 = U1_Modified_circuit(n_kernels=3, n_input_channels=12,activation='relu', datatype=datatype,
                      name='MODIFIED_CO_U1_QCNN')(x_input)

    if datatype == "COLORS" or datatype == "CIFAR10" or datatype == "COLORS_SHAPE":
        x_input = tf.keras.layers.Input((10,10,3), name = 'input')

        # Create an instance of U1_circuit
        u1_circuit_layer = U1_Modified_circuit(n_kernels=3, n_input_channels=3, activation='relu',
                                      datatype=datatype, name='MODIFIED_CO_U1_QCNN')

        # Print the circuit before applying the layer to the input
        print("Quantum Circuit:")
        print(u1_circuit_layer.circuit.to_text_diagram())
        plot_circuit(u1_circuit_layer.circuit)

        # Apply the circuit layer
        x_qconv1 = u1_circuit_layer(x_input)


    x_flatten = tf.keras.layers.Flatten()(x_qconv1)

    x_fc1 = tf.keras.layers.Dense(32, activation='relu')(x_flatten)

    if datatype == "COLORS":
        x_fc2 = tf.keras.layers.Dense(9, activation='softmax')(x_fc1)
    
    elif datatype == "COLORS_SHAPE":
        x_fc2 = tf.keras.layers.Dense(24, activation='softmax')(x_fc1)
    
    else:
        x_fc2 = tf.keras.layers.Dense(classes, activation='softmax')(x_fc1)

    return tf.keras.models.Model(inputs = x_input, outputs = x_fc2, name = 'MODIFIED_CO_U1_QCNN')

############################
def QCNN_U1_control_model(datatype,classes):

    if datatype=="CHANNELS":
        x_input = tf.keras.layers.Input((10,10,12), name = 'input')
    
    if datatype=="COLORS" or datatype == "CIFAR10" or datatype == "COLORS_SHAPE":
        x_input = tf.keras.layers.Input((10,10,3), name = 'input')
    
    x_qconv1 = Q_U1_control(n_kernels=3, activation=tf.keras.layers.Activation('relu'),datatype=datatype,
                      name='Control_U1_QCNN')(x_input)

    x_flatten = tf.keras.layers.Flatten()(x_qconv1)

    x_fc1 = tf.keras.layers.Dense(32, activation=tf.keras.layers.Activation('relu'))(x_flatten)

    if datatype == "COLORS":
        x_fc2 = tf.keras.layers.Dense(9, activation='softmax')(x_fc1)
    
    elif datatype == "COLORS_SHAPE":
        x_fc2 = tf.keras.layers.Dense(24, activation='softmax')(x_fc1)

    else:
        x_fc2 = tf.keras.layers.Dense(classes, activation='softmax')(x_fc1)

    return tf.keras.models.Model(inputs = x_input, outputs = x_fc2, name = 'Control_U1_QCNN')
############################
def QCNN_U1_weighted_control_model(datatype,classes):

    if datatype=="CHANNELS":
        x_input = tf.keras.layers.Input((10,10,12), name = 'input')
    
    if datatype=="COLORS" or datatype == "CIFAR10" or datatype == "COLORS_SHAPE":
        x_input = tf.keras.layers.Input((10,10,3), name = 'input')
    
    x_qconv1 = Q_U1_control(n_kernels=3, classical_weights=True, activation=tf.keras.layers.Activation('relu'),datatype=datatype,
                      name='WEV_U1_QCNN')(x_input)

    x_flatten = tf.keras.layers.Flatten()(x_qconv1)

    x_fc1 = tf.keras.layers.Dense(32, activation=tf.keras.layers.Activation('relu'))(x_flatten)

    if datatype == "COLORS":
        x_fc2 = tf.keras.layers.Dense(9, activation='softmax')(x_fc1)
    
    elif datatype == "COLORS_SHAPE":
        x_fc2 = tf.keras.layers.Dense(24, activation='softmax')(x_fc1)

    else:
        x_fc2 = tf.keras.layers.Dense(classes, activation='softmax')(x_fc1)

    return tf.keras.models.Model(inputs = x_input, outputs = x_fc2, name = 'WEV_U1_QCNN')
