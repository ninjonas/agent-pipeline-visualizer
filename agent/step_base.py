import os
import logging
from typing import Dict, Any, Optional

class StepBase:
    """Base class for all agent steps"""
    
    def __init__(self, step_id: str, input_dir: str, output_dir: str):
        self.step_id = step_id
        self.input_dir = input_dir
        self.output_dir = output_dir
        
        # Setup logging
        self.logger = logging.getLogger(f"agent.step.{step_id}")
        self.logger.setLevel(logging.INFO)
        
        # Add console handler if not already added
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def execute(self) -> bool:
        """
        Execute the step.
        
        This method should be overridden by subclasses.
        
        Returns:
            bool: True if the step was successful, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement execute()")
    
    def get_input_path(self, filename: str) -> str:
        """
        Get the full path to an input file.
        
        Args:
            filename: The name of the input file.
            
        Returns:
            str: The full path to the input file.
        """
        return os.path.join(self.input_dir, filename)
    
    def get_output_path(self, filename: str) -> str:
        """
        Get the full path to an output file.
        
        Args:
            filename: The name of the output file.
            
        Returns:
            str: The full path to the output file.
        """
        return os.path.join(self.output_dir, filename)
    
    def list_input_files(self) -> list:
        """
        List all files in the input directory.
        
        Returns:
            list: A list of filenames in the input directory.
        """
        if not os.path.exists(self.input_dir):
            return []
        
        return [f for f in os.listdir(self.input_dir) if os.path.isfile(os.path.join(self.input_dir, f))]
    
    def list_output_files(self) -> list:
        """
        List all files in the output directory.
        
        Returns:
            list: A list of filenames in the output directory.
        """
        if not os.path.exists(self.output_dir):
            return []
        
        return [f for f in os.listdir(self.output_dir) if os.path.isfile(os.path.join(self.output_dir, f))]
    
    def read_input_file(self, filename: str, default: Optional[str] = None) -> Optional[str]:
        """
        Read the contents of an input file.
        
        Args:
            filename: The name of the input file.
            default: The default value to return if the file does not exist.
            
        Returns:
            str: The contents of the file, or the default value if the file does not exist.
        """
        file_path = self.get_input_path(filename)
        
        if not os.path.exists(file_path):
            return default
        
        with open(file_path, "r") as f:
            return f.read()
    
    def write_output_file(self, filename: str, content: str) -> None:
        """
        Write content to an output file.
        
        Args:
            filename: The name of the output file.
            content: The content to write to the file.
        """
        file_path = self.get_output_path(filename)
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "w") as f:
            f.write(content)
    
    def copy_input_to_output(self, filename: str) -> bool:
        """
        Copy an input file to the output directory.
        
        Args:
            filename: The name of the input file.
            
        Returns:
            bool: True if the file was copied, False if the input file does not exist.
        """
        input_path = self.get_input_path(filename)
        
        if not os.path.exists(input_path):
            return False
        
        output_path = self.get_output_path(filename)
        
        with open(input_path, "r") as in_file:
            content = in_file.read()
        
        with open(output_path, "w") as out_file:
            out_file.write(content)
        
        return True
