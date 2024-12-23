import json
import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QDialog, QFormLayout, QDialogButtonBox, QMessageBox, QLineEdit, QComboBox, QColorDialog, QLabel
from PyQt5.QtCore import Qt
from utils import load_json, save_json

class VariableManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Variable Manager")
        self.base_directory = "E:/dev/projects/vfx/misc.tools/json_files"
        os.makedirs(self.base_directory, exist_ok=True)
        self.base_filename = os.path.join(self.base_directory, "variables")
        self.latest_file = f"{self.base_filename}_latest.json"
        self.variables = self.load_latest_variables()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Main table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Name", "Type", "Default Value", "Override Per Shot"])
        self.table.setEditTriggers(QTableWidget.AllEditTriggers)  # Allow editing in all columns except type
        self.table.itemChanged.connect(self.on_table_item_changed)  # Connect item changes
        layout.addWidget(self.table)

        # Disable editing for the "Type" column (index 1)
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

        # Buttons
        button_layout = QHBoxLayout()
        add_variable_button = QPushButton("Add Variable")
        add_variable_button.clicked.connect(self.add_variable)

        publish_button = QPushButton("Publish")
        publish_button.clicked.connect(self.publish_new_version)

        delete_row_button = QPushButton("Delete Selected Row")
        delete_row_button.clicked.connect(self.delete_selected_row)

        button_layout.addWidget(add_variable_button)
        button_layout.addWidget(publish_button)
        button_layout.addWidget(delete_row_button)
        layout.addLayout(button_layout)

        self.refresh_table()
        self.setLayout(layout)

    def handle_color_validation_in_table(self, row, column):
        """Handles color validation when a cell in the table is edited."""
        item = self.table.item(row, column)
        color_str = item.text().strip()

        # Validate the color input before updating the table
        if not self.validate_color_input(color_str):
            QMessageBox.warning(self, "Error", "Invalid value for color type. Please enter three integers (0-255) separated by commas. --- handle_color_validation_in_table ---")
            item.setBackground(QColor(255, 0, 0))  # Optionally change the background color to indicate error
            return False  # Prevent table update if validation fails
        
        # If validation is successful, update the variable dictionary and continue
        self.update_variable_from_table(row)
        return True

    def update_variable_from_table(self, row):
        """Update the variable dictionary after a valid color is entered."""
        # Retrieve the name, type, and value from the table for the specified row
        name_item = self.table.item(row, 0)
        type_item = self.table.item(row, 1)
        default_item = self.table.item(row, 2)

        name = name_item.text().strip()
        var_type = type_item.text().strip()
        default_value = default_item.text().strip()

        # Add the variable to the dictionary based on the type
        if var_type == "color":
            # Assuming the default_value is in 'r, g, b' format
            default_value = tuple(map(int, default_value.split(",")))

        self.variables[name] = {"type": var_type, "default": default_value, "overrides": {}}

    def validate_and_add_variable(self, name_input, type_input, default_input):
        """Validate input and add the new variable."""
        name = name_input.text().strip()
        var_type = type_input.currentText()

        # Validate the variable name
        if not name:
            QMessageBox.warning(self, "Error", "Variable name cannot be empty.")
            return
        if name in self.variables:
            QMessageBox.warning(self, "Error", f"Variable name '{name}' already exists.")
            return

        # Validate the default value based on the selected type
        try:
            if var_type == "integer":
                default_value = int(default_input.text().strip())
            elif var_type == "float":
                default_value = float(default_input.text().strip())
            elif var_type == "boolean":
                default_value = default_input.currentText() == "True"
            elif var_type == "color":
                color_value = default_input.text().strip()
                if not self.validate_color_input(color_value):
                    raise ValueError("Invalid color input. Please enter three integers (0-255) separated by commas.")
                default_value = tuple(map(int, color_value.split(",")))
            elif var_type == "vector":
                # Extract values from the tuple of QLineEdits
                vector_values = [float(input_field.text().strip()) for input_field in default_input]
                if len(vector_values) != 3:
                    raise ValueError("Vector must have exactly three float values (X, Y, Z).")
                default_value = vector_values
            else:
                default_value = default_input.text().strip()
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
            return

        # Add the variable to the dictionary
        self.variables[name] = {"type": var_type, "default": default_value, "overrides": {}}

        # Refresh the table
        self.refresh_table()

        # Print for debugging
        print(f"Variable added: {name} of type {var_type} with default {default_value}")

        # Accept the dialog
        dialog = None
        if isinstance(default_input, tuple):  # For vector type, get the parent dialog from one of the inputs
            dialog = default_input[0].window()
        else:
            dialog = default_input.window()

        if isinstance(dialog, QDialog):
            dialog.accept()

    def validate_color_input(self, color_str):
        """Validates that the color string is in the correct format: 'R,G,B'."""
        print(f"Validating color input: {color_str}")  # Debugging line
        color_parts = color_str.split(",")
        
        # Debugging line to print split parts
        print(f"Parsed color values: {color_parts}")
        
        if len(color_parts) != 3:
            return False
        
        try:
            # Try to convert each part to an integer and ensure they are within the range 0-255
            r, g, b = map(int, [part.strip() for part in color_parts])
            print('r is a type', type(r), r)
            print('g is a type', type(g), g)
            print('b is a type', type(b), b)
            if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                print('all good till here')
                return True
            else:
                return False
        except ValueError:
            return False

    def load_latest_variables(self):
        """Load the latest variables from the latest JSON file."""
        if os.path.exists(self.latest_file):
            return load_json(self.latest_file).get("variables", {})
        return {}

    def save_to_file(self, filename):
        """Save the current variables to a specified file in JSON format."""
        data = {"variables": self.variables}
        save_json(data, filename)

    def get_next_version_filename(self):
        """Determine the next versioned filename with 3-digit formatting."""
        version = 1
        while os.path.exists(f"{self.base_filename}_v{version:03d}.json"):
            version += 1
        return f"{self.base_filename}_v{version:03d}.json"

    def publish_new_version(self):
        """Publish the current variables as a new version and update the 'latest' file."""
        versioned_file = self.get_next_version_filename()
        self.save_to_file(versioned_file)
        self.save_to_file(self.latest_file)
        QMessageBox.information(self, "Success", f"Published new version: {versioned_file}")

    def refresh_table(self):
        """Update the main table with current variables."""
        self.table.setRowCount(0)
        for name, data in self.variables.items():
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Name column (editable by default)
            self.table.setItem(row, 0, QTableWidgetItem(name))

            # Type column (non-editable)
            type_item = QTableWidgetItem(data["type"])
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, type_item)

            # Default value column (editable by default)
            self.table.setItem(row, 2, QTableWidgetItem(str(data["default"])))

            # Manage Overrides button
            button = QPushButton("Manage Overrides")
            button.clicked.connect(lambda _, n=name: self.manage_overrides(n))
            self.table.setCellWidget(row, 3, button)

    def delete_selected_row(self):
        """Delete the selected row in the main table."""
        selected_row = self.table.currentRow()
        if selected_row != -1:
            variable_name = self.table.item(selected_row, 0).text()
            if variable_name in self.variables:
                del self.variables[variable_name]
                self.table.removeRow(selected_row)
                QMessageBox.information(self, "Success", f"Variable '{variable_name}' deleted.")
            else:
                QMessageBox.warning(self, "Error", f"Variable '{variable_name}' not found.")
        else:
            QMessageBox.warning(self, "Error", "No row selected for deletion.")

    def add_variable(self):
        """Add a new variable through a dialog with validation."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Variable")

        form_layout = QFormLayout()

        name_input = QLineEdit()
        type_input = QComboBox()
        type_input.addItems(["string", "integer", "float", "boolean", "color", "vector"])

        self.default_input_container = QVBoxLayout()
        self.current_default_input = QLineEdit()  # Default input widget
        self.default_input_container.addWidget(self.current_default_input)

        def update_default_input():
            """Update the input field based on the selected type."""
            # Clear existing widgets
            while self.default_input_container.count():
                item = self.default_input_container.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

            selected_type = type_input.currentText()
            if selected_type == "color":
                # Create color picker button for color input
                color_button = QPushButton("Select Color")
                color_button.clicked.connect(self.select_color)
                self.default_input_container.addWidget(color_button)
                self.current_default_input = color_button
            elif selected_type == "vector":
                x_input = QLineEdit()
                x_input.setPlaceholderText("x")
                y_input = QLineEdit()
                y_input.setPlaceholderText("y")
                z_input = QLineEdit()
                z_input.setPlaceholderText("z")
                vector_layout = QHBoxLayout()
                vector_layout.addWidget(x_input)
                vector_layout.addWidget(y_input)
                vector_layout.addWidget(z_input)
                self.default_input_container.addLayout(vector_layout)
                self.current_default_input = (x_input, y_input, z_input)
            elif selected_type == "boolean":
                boolean_input = QComboBox()
                boolean_input.addItems(["True", "False"])
                self.default_input_container.addWidget(boolean_input)
                self.current_default_input = boolean_input
            else:
                default_input = QLineEdit()
                self.default_input_container.addWidget(default_input)
                self.current_default_input = default_input

        type_input.currentIndexChanged.connect(update_default_input)

        form_layout.addRow("Name:", name_input)
        form_layout.addRow("Type:", type_input)
        form_layout.addRow("Default Value:", self.default_input_container)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(lambda: self.validate_and_add_variable(name_input, type_input, self.current_default_input))
        buttons.rejected.connect(dialog.reject)

        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(buttons)
        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            # After the dialog is accepted, ensure the variable is added correctly
            self.refresh_table()

    def select_color(self):
        """Open the color picker dialog and set the color."""
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_default_input.setText(f"{color.red()}, {color.green()}, {color.blue()}")
            print(f"Selected color value: {color.red()}, {color.green()}, {color.blue()}")

    def manage_overrides(self, variable_name):
        """Open a dialog to manage overrides for a specific variable."""
        if variable_name not in self.variables:
            QMessageBox.warning(self, "Error", "Variable not found!")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Manage Overrides for {variable_name}")

        # Layout for overrides
        layout = QVBoxLayout()

        # Table to show existing overrides
        overrides_table = QTableWidget(0, 2)
        overrides_table.setHorizontalHeaderLabels(["Shot", "Value"])
        overrides_table.setEditTriggers(QTableWidget.AllEditTriggers)  # Allow editing in all columns
        overrides_table.itemChanged.connect(lambda item: self.on_override_item_changed(variable_name, item, overrides_table))  # Connect item changes
        layout.addWidget(overrides_table)

        # Populate table with existing overrides
        variable_data = self.variables[variable_name]
        for shot, value in variable_data.get("overrides", {}).items():
            row = overrides_table.rowCount()
            overrides_table.insertRow(row)
            overrides_table.setItem(row, 0, QTableWidgetItem(shot))
            overrides_table.setItem(row, 1, QTableWidgetItem(str(value)))

        # Add new override input fields
        shot_input = QLineEdit()
        shot_input.setPlaceholderText("Shot (e.g., shot01)")

        value_input = QLineEdit()
        value_input.setPlaceholderText("Override Value")

        add_override_button = QPushButton("Add/Update Override")
        add_override_button.clicked.connect(lambda: self.add_or_update_override(variable_name, shot_input, value_input, overrides_table))

        delete_override_button = QPushButton("Delete Selected Override")
        delete_override_button.clicked.connect(lambda: self.delete_selected_override(variable_name, overrides_table))

        layout.addWidget(QLabel("Add/Update Override:"))
        layout.addWidget(shot_input)
        layout.addWidget(value_input)
        layout.addWidget(add_override_button)
        layout.addWidget(delete_override_button)

        # Dialog buttons
        dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        dialog_buttons.accepted.connect(dialog.accept)
        dialog_buttons.rejected.connect(dialog.reject)
        layout.addWidget(dialog_buttons)

        dialog.setLayout(layout)

        # Open the dialog
        dialog.exec_()

    def delete_selected_override(self, variable_name, overrides_table):
        """Delete the selected override from the table and dictionary."""
        selected_row = overrides_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Error", "No override selected for deletion!")
            return

        shot = overrides_table.item(selected_row, 0).text()

        # Remove the override from the dictionary
        if shot in self.variables[variable_name]["overrides"]:
            del self.variables[variable_name]["overrides"][shot]
            QMessageBox.information(self, "Success", f"Override for shot '{shot}' deleted.")
            self.refresh_overrides_table(variable_name, overrides_table)
        else:
            QMessageBox.warning(self, "Error", "Override not found.")

    def refresh_overrides_table(self, variable_name, overrides_table):
        """Refresh the overrides table to reflect the current state."""
        overrides_table.setRowCount(0)
        for shot, value in self.variables[variable_name].get("overrides", {}).items():
            row = overrides_table.rowCount()
            overrides_table.insertRow(row)
            overrides_table.setItem(row, 0, QTableWidgetItem(shot))
            overrides_table.setItem(row, 1, QTableWidgetItem(str(value)))

    def add_or_update_override(self, variable_name, shot_input, value_input, overrides_table):
        """Add or update an override for a specific variable."""
        shot = shot_input.text().strip()
        value = value_input.text().strip()

        # Validate the value based on the variable type
        variable_type = self.variables[variable_name]["type"]

        try:
            if variable_type == "boolean":
                # Validate boolean value
                if value.lower() not in ["true", "false"]:
                    raise ValueError("Invalid boolean value. Please enter 'True' or 'False'.")
                value = value.lower() == "true"
            elif variable_type == "color":
                # Validate color value (RGB format)
                value = self.validate_color(value)
            elif variable_type == "vector":
                # Validate vector value (X, Y, Z)
                value = self.validate_vector(value)
            elif variable_type == "integer":
                # Validate integer value
                value = int(value)
            elif variable_type == "float":
                # Validate float value
                value = float(value)
            else:
                # For string type, no specific validation
                pass
            
            # Add or update the override
            self.variables[variable_name]["overrides"][shot] = value

            # Update the table with the new or updated override
            for row in range(overrides_table.rowCount()):
                if overrides_table.item(row, 0).text() == shot:
                    overrides_table.setItem(row, 1, QTableWidgetItem(str(value)))
                    return
            
            # If no existing override, add a new one
            row = overrides_table.rowCount()
            overrides_table.insertRow(row)
            overrides_table.setItem(row, 0, QTableWidgetItem(shot))
            overrides_table.setItem(row, 1, QTableWidgetItem(str(value)))

        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
            return

    def validate_color(self, value):
        """Validate and parse the color input (RGB format)."""
        try:
            value = value.replace("(", "").replace(")", "").replace("[", "").replace("]", "")
            color_parts = [int(x.strip()) for x in value.split(",")]
            if len(color_parts) != 3:
                raise ValueError("Color must have three values separated by commas (e.g., 255, 0, 0).")
            
            color_value = tuple(x for x in color_parts)
            if not all(0 <= x <= 255 for x in color_value):
                raise ValueError("Each color component must be between 0 and 255.")
            
            return color_parts
        
        except Exception as e:
            raise ValueError(f"Invalid color format: {e}")

    def validate_vector(self, value):
        """Validate and parse the vector input (X, Y, Z)."""
        try:
            value = value.replace("(", "").replace(")", "").replace("[", "").replace("]", "")
            vector_parts = [float(x.strip()) for x in value.split(",")]

            if len(vector_parts) != 3:
                raise ValueError("Vector must have three values (X, Y, Z) separated by commas.")

            return vector_parts

        except Exception as e:
            raise ValueError(f"Invalid vector format: {e}")

    def on_table_item_changed(self, item):
        """Handle the event when an item in the main table is edited."""
        row = item.row()
        column = item.column()
        variable_name = self.table.item(row, 0).text()

        # Block signals temporarily to prevent recursion
        self.table.blockSignals(True)

        print(f"Editing row {row}, column {column} for variable '{variable_name}'")  # Debugging

        if column == 2:  # Default Value column
            new_value = item.text()
            print(f"New value entered: {new_value}")  # Debugging

            # Get the variable type
            var_type = self.variables[variable_name]["type"]
            print(f"Variable type: {var_type}")  # Debugging

            # Validate the default value based on type
            if var_type == "boolean":
                if new_value.lower() not in ["true", "false"]:
                    print(f"Invalid boolean value: {new_value}")  # Debugging
                    QMessageBox.warning(self, "Error", "Invalid value for boolean type. Please enter 'True' or 'False'.")
                    item.setText(str(self.variables[variable_name]["default"]))  # Revert to the old value
                    self.table.blockSignals(False)  # Re-enable signals
                    return
                else:
                    self.variables[variable_name]["default"] = new_value.lower() == "true"
                    print(f"Updated boolean default value to: {self.variables[variable_name]['default']}")  # Debugging

            elif var_type == "color":
                try:
                    # Remove parentheses or brackets if they exist
                    new_value = new_value.replace("(", "").replace(")", "").replace("[", "").replace("]", "")
                    color_parts = [x.strip() for x in new_value.split(",")]
                    print(f"Processed color parts: {color_parts}")  # Debugging

                    # Ensure there are exactly 3 values (RGB)
                    if len(color_parts) != 3:
                        raise ValueError("Color must have three values separated by commas (e.g. 255, 0, 0).")

                    # Convert parts to integers and validate range
                    value = tuple(int(x) for x in color_parts if 0 <= int(x) <= 255)
                    if len(value) != 3:
                        raise ValueError("Each color component must be between 0 and 255.")

                    # Update the variable with the new color value
                    self.variables[variable_name]["default"] = value
                    item.setText(f"[{', '.join(map(str, value))}]")
                    print(f"Updated color default value to: {value}")  # Debugging

                except ValueError as e:
                    print(f"Error parsing color: {str(e)}")  # Debugging
                    QMessageBox.warning(self, "Error", f"Invalid value for color type. {str(e)}")
                    item.setText(str(self.variables[variable_name]["default"]))  # Revert to the old value
                    self.table.blockSignals(False)  # Re-enable signals
                    return

            elif var_type == "vector":
                try:
                    # Remove any extra spaces and split by commas
                    new_value = new_value.replace("(", "").replace(")", "").replace("[", "").replace("]", "")
                    vector_parts = [float(x.strip()) for x in new_value.split(",")]
                    print(f"Processed vector parts: {vector_parts}")  # Debugging

                    if len(vector_parts) != 3:
                        raise ValueError("Vector must have three values (X, Y, Z) separated by commas.")

                    # Update the variable with the new vector value
                    self.variables[variable_name]["default"] = vector_parts
                    item.setText(f"[{', '.join(map(str, vector_parts))}]")
                    print(f"Updated vector default value to: {vector_parts}")  # Debugging

                except ValueError:
                    print(f"Invalid vector input: {new_value}")  # Debugging
                    QMessageBox.warning(self, "Error", "Invalid value for vector type. Please enter three numbers (X, Y, Z) separated by commas.")
                    item.setText(str(self.variables[variable_name]["default"]))  # Revert to the old value
                    self.table.blockSignals(False)  # Re-enable signals
                    return

            elif var_type == "integer":
                try:
                    self.variables[variable_name]["default"] = int(new_value)
                    print(f"Updated integer default value to: {self.variables[variable_name]['default']}")  # Debugging
                except ValueError:
                    print(f"Invalid integer input: {new_value}")  # Debugging
                    QMessageBox.warning(self, "Error", "Invalid value for integer type. Please enter an integer.")
                    item.setText(str(self.variables[variable_name]["default"]))  # Revert to the old value
                    self.table.blockSignals(False)  # Re-enable signals
                    return

            elif var_type == "float":
                try:
                    self.variables[variable_name]["default"] = float(new_value)
                    print(f"Updated float default value to: {self.variables[variable_name]['default']}")  # Debugging
                except ValueError:
                    print(f"Invalid float input: {new_value}")  # Debugging
                    QMessageBox.warning(self, "Error", "Invalid value for float type. Please enter a float.")
                    item.setText(str(self.variables[variable_name]["default"]))  # Revert to the old value
                    self.table.blockSignals(False)  # Re-enable signals
                    return

            else:
                # For string type, no validation needed
                self.variables[variable_name]["default"] = new_value
                print(f"Updated string default value to: {new_value}")  # Debugging

        # Re-enable signals after processing the change
        self.table.blockSignals(False)

    def on_override_item_changed(self, variable_name, item, overrides_table):
        """Handle the event when an override item is edited."""
        shot = overrides_table.item(item.row(), 0).text()
        value = item.text()

        if shot in self.variables[variable_name]["overrides"]:
            self.variables[variable_name]["overrides"][shot] = value