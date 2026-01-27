import tkinter as tk
from tkinter import ttk, messagebox
import RPi.GPIO as GPIO

class GPIOConfigMenu:
    def __init__(self, root):
        self.root = root
        self.root.title("Raspberry Pi GPIO Configuration")
        self.root.geometry("500x600")
        
        # Dictionary to store GPIO states
        self.gpio_states = {}
        
        # Raspberry Pi GPIO pins (BCM numbering)
        self.gpio_pins = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]
        
        # Initialize GPIO states
        for pin in self.gpio_pins:
            self.gpio_states[pin] = tk.StringVar(value="unused")
        
        self.create_widgets()
    
    def create_widgets(self):
        # Title
        title_label = ttk.Label(self.root, text="GPIO Pin Configuration", font=("Arial", 14, "bold"))
        title_label.pack(pady=10)
        
        # Frame for canvas and scrollbar
        frame = ttk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Canvas for scrollable content
        canvas = tk.Canvas(frame, bg="white")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create GPIO configuration rows
        for pin in self.gpio_pins:
            self.create_gpio_row(scrollable_frame, pin)
        
        canvas.pack(side="left", fill=tk.BOTH, expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Button frame
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)
        
        # Apply button
        apply_btn = ttk.Button(button_frame, text="Apply Configuration", command=self.apply_config)
        apply_btn.pack(side=tk.LEFT, padx=5)
        
        # Reset button
        reset_btn = ttk.Button(button_frame, text="Reset", command=self.reset_config)
        reset_btn.pack(side=tk.LEFT, padx=5)
        
        # Exit button
        exit_btn = ttk.Button(button_frame, text="Exit", command=self.root.quit)
        exit_btn.pack(side=tk.LEFT, padx=5)
    
    def create_gpio_row(self, parent, pin):
        # Create a frame for each GPIO pin
        pin_frame = ttk.Frame(parent, relief=tk.SUNKEN, borderwidth=1)
        pin_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Pin label
        pin_label = ttk.Label(pin_frame, text=f"GPIO {pin}", width=10, font=("Arial", 10, "bold"))
        pin_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Radio buttons for selection
        ttk.Radiobutton(pin_frame, text="Unused", variable=self.gpio_states[pin], value="unused").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(pin_frame, text="Input", variable=self.gpio_states[pin], value="input").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(pin_frame, text="Output", variable=self.gpio_states[pin], value="output").pack(side=tk.LEFT, padx=5)
    
    def apply_config(self):
        # Display current configuration
        config_text = "GPIO Configuration:\n\n"
        inputs = []
        outputs = []
        
        for pin in self.gpio_pins:
            state = self.gpio_states[pin].get()
            if state == "input":
                inputs.append(pin)
            elif state == "output":
                outputs.append(pin)
        
        if inputs:
            config_text += f"Input Pins: {inputs}\n"
        if outputs:
            config_text += f"Output Pins: {outputs}\n"
        if not inputs and not outputs:
            config_text += "No pins configured."
        
        messagebox.showinfo("Configuration Applied", config_text)
        
        # You can add actual GPIO setup code here
        print("Configuration Applied:")
        if inputs:
            print(f"Input Pins: {inputs}")
        if outputs:
            print(f"Output Pins: {outputs}")
    
    def reset_config(self):
        # Reset all GPIO states to unused
        for pin in self.gpio_pins:
            self.gpio_states[pin].set("unused")
        messagebox.showinfo("Reset", "All GPIO pins reset to unused.")

def main():
    root = tk.Tk()
    app = GPIOConfigMenu(root)
    root.mainloop()

if __name__ == "__main__":
    main()
