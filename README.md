# Quantum Convolutional Neural Networks for Multi-Channel Image Processing

---

## **Abstract**
This repository implements the paper ["Quantum Convolutional Neural Networks for Multi-Channel Image Processing"](link_to_paper) using TensorFlow Quantum. The project demonstrates how quantum computing techniques can be applied to image processing tasks, focusing on multi-channel datasets like CIFAR-10. This implementation includes the Weighted Entanglement Variance (WEV) model and the Controlled Output (CO) model, with a modified version of the CO circuit. The modification entangles all four qubits with the ancillary qubit, enhancing phase entanglement mechanisms. This repository explores their performance against control QCNN.

---

## **Architecture**
The project implements several quantum convolutional circuits, including the CO circuit, the modified CO circuit, and the WEV circuit. These circuits leverage ancillary qubits, phase gates, and controlled entanglement mechanisms to process multi-channel image data. Hybrid quantum-classical machine learning architecture used to evaluate each of the proposed circuits.

![image](https://github.com/user-attachments/assets/fb93305d-28b0-4f0d-9a67-5108a8462dde)

### **Modified Channel Overwrite (CO) circuit**


---

## **Results**
The following results were obtained by training the WEV-QCNN and modified CO-QCNN models on the CIFAR-10 using 3 classes:

### **Test Accuracy:**
- **CONTROL-QCNN:** ~64.6% (on 3-class CIFAR-10)
- **WEV-QCNN:** ~75.6% (on 3-class CIFAR-10)
- **CO-QCNN:** ~80.03% (on 3-class CIFAR-10)
- **Modified CO-QCNN:** ~81.6% (on 3-class CIFAR-10)

### **Learning Curves**
![Learning Curves](images/learning_curves.png "Model Learning Curves")

### **Confusion Matrix for Modified CO-QCNN**
![Confusion Matrix](images/modified_co_confusion_matrix.png "Confusion Matrix for Modified CO-QCNN")

---

## **Project Report**
The detailed project report includes:
- Implementation details
- Challenges faced
- Results and analysis

### **Access the Report**
[View the Project Report](docs/project_report.pdf)

> **Note:** Place the project report in a `docs/` folder in your repository’s root directory for the above link to work correctly.

---

## **Libraries Used**
The following libraries were essential for this project:
- `tensorflow==2.15.0` (TensorFlow for model training and backend computation)
- `tensorflow-quantum` (Quantum machine learning library)
- `cirq==1.3.0` (Quantum circuit simulation and visualization)
- `numpy` (Numerical computations)
- `scikit-learn` (Confusion matrix computation)
- `matplotlib` (Visualization of learning curves and confusion matrix)
- `pydot` (Required for model visualization)
- `graphviz` (Dependency for pydot)

---

## **Folder Structure**
```
repo/
├── circuits.py        # Quantum circuit implementations
├── models.py          # Quantum and classical model definitions
├── train.py           # Training script with menu-driven options
├── utils.py           # Utility functions
├── create_noisy_colors.py  # Synthetic dataset creation
├── output/            # Output folder containing results and plots
├── docs/              # Documentation folder for the project report
│   └── project_report.pdf
├── images/            # Images for the README and results
└── requirements.txt   # Required libraries for the project
```

---

## **Running the Project**

### **1. Prerequisites**
- Docker (recommended)
- Python 3.9

### **2. Installation**
Install the required libraries:
```bash
pip install -r requirements.txt
```

### **3. Run the Training Script**
To train a model, execute the following command:
```bash
python train.py
```
Follow the menu-driven options to:
1. Select the dataset (e.g., CIFAR-10).
2. Choose the number of classes.
3. Set the learning rate.
4. Select the model (e.g., WEV-QCNN or Modified CO-QCNN).

### **4. Using Docker to Run the Project**

#### **Step 1: Build the Docker Image**
Create a `Dockerfile` with the required dependencies and build the image:
```bash
docker build -t qcnn_project .
```

#### **Step 2: Run the Docker Container**
Run the container with a mounted volume for accessing local files:
```bash
docker run -it -v $(pwd):/app qcnn_project bash
```
This mounts your current working directory to `/app` in the container.

#### **Step 3: Train the Models in the Container**
Once inside the container, execute:
```bash
python train.py
```
Follow the prompts as described above.

### **5. Results**
- Output files will be stored in the `output/` folder with timestamps.
- Includes learning curves, confusion matrices, and saved models.

---

## **References**
- **Paper Implemented:** ["Quantum Convolutional Neural Networks for Multi-Channel Image Processing"](link_to_paper)
- **TensorFlow Quantum Documentation:** [TFQ Docs](https://www.tensorflow.org/quantum)
- **Cirq Documentation:** [Cirq Docs](https://quantumai.google/cirq)

---

**Author:** [Your Name]

