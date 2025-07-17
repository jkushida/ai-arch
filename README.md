# FEM Analysis and AI-Driven Parametric Architectural Design Optimization

## Overview
This repository manages lecture materials on parametric architectural design optimization using FEM analysis and AI technologies. Students will learn data-driven design methodologies to simultaneously satisfy complex architectural requirements.

## Addressing Complexity in Architectural Design
Architectural design must simultaneously satisfy the following conflicting requirements:
- **Structural Safety**: Resistance to earthquakes and wind loads
- **Economy**: Minimization of construction and maintenance costs
- **Environmental Performance**: Reduction of CO2 emissions
- **Living Comfort**: Natural lighting, ventilation, and spatial openness
- **Constructability**: Ease of construction and project duration

## Course Content

### 1. Introduction to Parametric Design
- **Traditional Design vs Parametric Design**
  - Traditional: Fixed geometry, manual drawing revisions, limited design alternatives, experience-based decisions
  - Parametric: Variable geometry, automatic parameter updates, infinite design possibilities, data-driven optimization
- **Definition**: A design methodology where geometry and performance automatically change based on parameters (variables)

### 2. FEM (Finite Element Method) Analysis
- **What is FEM**: A method to analyze complex structures by dividing them into small "elements"
- **Parametric Design Evaluation**
  - Parameter changes → Shape variations → Automatic structural performance evaluation
  - Automatic analysis of arbitrary 3D shapes
  - Detailed visualization of stress distributions
  - Automatic calculation of evaluation metrics

### 3. FEM Analysis Implementation with FreeCAD
- **FreeCAD Features**
  - Open-source 3D CAD software
  - Parametric modeling support
  - Automation via Python scripting
  - Built-in FEM workbench (using CalculiX)
- **Scripted Analysis Workflow**
  1. Model creation (Part::Box, etc.)
  2. Analysis container generation
  3. Material, constraint, and load definition (Python dictionaries)
  4. Mesh generation (Netgen)
  5. Solver setup & execution (CalculiX)
  6. Result retrieval and storage
- **FEM Analysis Outputs**
  - Stress: Von Mises stress, principal stresses, component stresses (Sxx, etc.)
  - Displacement: Nodal displacements (X, Y, Z), displacement vector magnitude
  - Strain: Principal strains, directional strains
  - Reaction forces: Forces at constrained surfaces
  - Mesh: Element count, node count, element shapes
  - Visualization: Stress distribution plots, deformed shape diagrams, animations

### 4. Architectural Design Application Example
- **Building Parameter Settings (Example)**
  - 1st floor: Piloti (columns only)
  - 2nd floor: Enclosed living space with walls
  - Roof: Parametric barrel vault
  - Stairs: L-shaped external staircase
  - Number of variables: 9

### 5. AI Optimization Algorithms
- **Optimization Workflow (PSO, etc.)**
  1. Set cost minimization as objective function
  2. Verify safety factor of solutions
  3. Search for minimum cost solution satisfying safety factor >= 2
  4. Constrain design variables within defined domains to narrow search space
- **Implemented Algorithms**
  - Particle Swarm Optimization (PSO)
  - Genetic Algorithm (GA)
  - Differential Evolution (DE)
  - Multi-objective optimization

### 6. Implementation Technologies
- Automation using Python/FreeCAD
- Parametric modeling
- Optimization algorithm implementation
- Result visualization and analysis

## Directory Structure
```
ai-arch/
├── files/              # Lecture materials and sample codes
├── lectures/          # Lecture slides
├── examples/          # Implementation examples
├── datasets/          # Sample datasets
└── projects/          # Student projects
```

## Technologies Used
- **Programming Language**: Python
- **CAD Software**: FreeCAD
- **Optimization Libraries**: scipy, pymoo
- **Machine Learning**: scikit-learn, TensorFlow
- **Visualization**: matplotlib, plotly

## Target Audience
- Architecture students (3rd-4th year undergraduates, graduate students)
- Architecture practitioners interested in AI technologies
- No programming experience required (learning from basics)

## References
- Publications from the Society of Architectural Information
- Fundamental literature on AI and machine learning
- Textbooks on optimization algorithms

## License
Free for educational use. Please contact us individually for commercial use.

## Contact
For questions or suggestions, please create an Issue or contact us directly.

---
*AI-powered architectural design experiments*