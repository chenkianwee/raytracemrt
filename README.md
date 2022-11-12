# raytracemrt
Python codes to calculate the Mean Radiant Temperature from thermal scans and geometry point cloud

## Getting started
These instructions on written for Python on windows.
1. Install Python 3.11 (https://www.python.org/)
2. Create a virtual environment with 'py -m venv ray' this will create a virtual environment in the directory ray of your current directory (https://realpython.com/python-virtual-environments-a-primer/#deactivate-it)
3. Activate the environment ray\Scripts\activate
4. 'pip install raytracemrt'
6. download the example file here: 'https://github.com/chenkianwee/raytracemrt/tree/main/example/ply' right click on the file and 'save link as'
7. execute the program with the example with these parameters:
    ```
    raytracemrt -s your/directory/example1_therm.ply -x 0 0 1.5 -d 4 5 3.5 -z 0.3 -g 0.5 0.5 1 0.5 
    ```
8. go to the directory where you have downloaded the example file. All the results will be in a folder called 'example1_therm_result'.
9. the folder will have 5 folders to store all the intermediate results. Check the mrt folder to get the mrt results.
