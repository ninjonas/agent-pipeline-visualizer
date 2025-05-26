import os
from typing import Optional
from loguru import logger

class StepBase:
    """Base class for all agent steps"""
    
    def __init__(self, step_id: str, input_dir: str, output_dir: str):
        self.step_id = step_id
        self.input_dir = input_dir
        self.output_dir = output_dir
    
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
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeError as e:
            logger.error(f"UnicodeError reading input file {file_path}: {e}")
            return default
        except OSError as e: # Catches IOError as well
            logger.error(f"OS error reading input file {file_path}: {e}")
            return default
    
    def write_output_file(self, filename: str, content: str) -> None:
        """
        Write content to an output file.
        
        Args:
            filename: The name of the output file.
            content: The content to write to the file.
        """
        file_path = self.get_output_path(filename)
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        except UnicodeError as e:
            logger.error(f"UnicodeError writing output file {file_path}: {e}")
        except OSError as e: # Catches IOError as well
            logger.error(f"OS error writing output file {file_path}: {e}")
    
    def copy_input_to_output(self, filename: str) -> bool:
        """
        Copy an input file to the output directory.
        
        Args:
            filename: The name of the input file.
            
        Returns:
            bool: True if the file was copied, False if the input file does not exist or an error occurred.
        """
        input_path = self.get_input_path(filename)
        
        if not os.path.exists(input_path):
            logger.warning(f"Input file {input_path} not found for copy.")
            return False
        
        output_path = self.get_output_path(filename)
        
        try:
            with open(input_path, "r", encoding="utf-8") as in_file:
                content = in_file.read()
            
            with open(output_path, "w", encoding="utf-8") as out_file:
                out_file.write(content)
            return True
        except UnicodeError as e:
            logger.error(f"UnicodeError copying file from {input_path} to {output_path}: {e}")
            return False
        except OSError as e: # Catches IOError as well
            logger.error(f"OS error copying file from {input_path} to {output_path}: {e}")
            return False
