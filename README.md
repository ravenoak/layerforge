# LayerForge
A 3D Model Slicing and SVG Generation Application

## Overview
This application slices a 3D model (STL file) into layers and generates SVG files for each layer, including reference
marks for reassembly.

## Project Goals
1. Adhere to the functional requirements.
2. Implement the application in Python.
3. Bundle the application and its dependencies into a single executable.
4. Ensure the executable runs on different platforms without requiring a Python installation.
5. Utilize Single Responsibility Principle (SRP) and Separation of Concerns (SoC) in the design.
6. Implement a clean and maintainable codebase.

## Project Requirements

### Functional Requirements
1. **Load 3D Model**:
   - Read an STL file and load the model.

2. **Scaling**:
   - Scale the model using either a multiplier or a target height while maintaining aspect ratios.

3. **Slicing**:
   - Slice the model into layers of a specified thickness.

4. **Reference Marks**:
   - Reference marks should be placed at the centroid of each slice, where appropriate.
   - Reference marks should be inherited from adjacent slices where possible, including the shape of the mark.
   - New reference marks should be a different shape when added to a slice where they are not inherited.
   - Ensure marks are aligned with adjacent slices.
   - Marks must not overlap and must be inside the model's contours.
   - Marks must not be placed on the contour's edges.
   - Marks must not exceed the contour's boundaries.
   - The distance between marks should be within the scale of the overall model.
   - The size of the marks should be proportional to the model's scale, while maintaining visibility.
   - The marks need to be able to be used to properly align the slices during reassembly, including rotational alignment
     in addition to translational alignment.

5. **SVG Generation**:
   - Generate an SVG file for each slice.
   - Include contours, reference marks, and slice numbers.
   - Each slice should be labeled with its number within the contour area.

### Non-Functional Requirements
- The application should bundle all dependencies to mimic a statically compiled binary.
- The executable should run on different platforms without requiring a Python installation.

## Pseudocode

1. Load the 3D Model:  
   1. Read an STL file to load the model into the application.
2. Scale the Model:  
   1. If a scale factor is provided, scale the model by this factor.
   2. If a target height is provided, calculate the necessary scale factor to achieve this height and apply it to the
      model, ensuring the aspect ratios are maintained.
3. Calculate the Model Origin:  
   1. Determine the model's origin point for reference in subsequent operations.
4. Slice the Model into Layers:  
   1. Determine the positions for each slice based on the specified layer height.
   2. For each determined position:
      1. Slice the model at this position.
      2. Project the resulting slice to a 2D plane.
      3. Create a MultiPolygon representing the 2D contours of the slice.
5. For each slice, process the slice:
   1. Calculate Reference Marks:
      1. Retrieve potential reference marks based on the centroids of the slice's contours.
      2. Use the ReferenceMarkManager to find the closest existing mark within a tolerance or create a new mark if none
         is sufficiently close, ensuring:
         * Marks are inherited from adjacent slices where possible.
         * New marks are assigned a unique shape if not inherited.
         * Marks do not overlap and are contained within the model's contours.
         * Marks are not placed on the model's edges.
         * The distance between marks is appropriate for the model's scale.
         * The size of the marks is proportional to the model's scale, ensuring visibility.
   2. Adjust Reference Marks:
      1. Adjust the positions of the reference marks to avoid overlaps, using the ReferenceMarkAdjuster.
   3. Generate SVG File:
      1. Draw the slice contours.
      2. Add the adjusted reference marks.
      3. Annotate the slice with its number within the contour area.
6. Output:  
   1. Save the generated SVG files to the specified output directory, with each file representing a slice of the
      original 3D model.

## Usage
1. Place the STL file in the project directory.
2. Set the desired layer height and scale parameters.
3. Run the application.
4. Find the generated SVG files in the specified output directory.
