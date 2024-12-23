import sys
from PyQt5.QtWidgets import QApplication
from variable_manager import VariableManager

def main():
    app = QApplication(sys.argv)
    window = VariableManager()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
