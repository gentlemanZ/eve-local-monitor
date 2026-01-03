"""GUI tool for selecting screen region via click-and-drag."""

import tkinter as tk
from tkinter import messagebox
from PIL import ImageGrab, ImageTk
import configparser
import os


class RegionSelector:
    """Interactive region selector with click-and-drag interface."""

    def __init__(self):
        """Initialize the region selector."""
        self.root = None
        self.canvas = None
        self.screenshot = None
        self.photo = None
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.selected_region = None

    def select_region(self):
        """
        Launch GUI to select screen region via click-and-drag.

        Returns:
            tuple: (left, top, right, bottom) or None if cancelled
        """
        # Take fullscreen screenshot
        self.screenshot = ImageGrab.grab()

        # Create fullscreen window
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.configure(cursor='crosshair')

        # Create canvas with screenshot
        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Display screenshot
        self.photo = ImageTk.PhotoImage(self.screenshot)
        self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        # Add instructions
        instructions = (
            "Click and drag to select the EVE Local player list region\n"
            "Press ESC to cancel"
        )
        self.canvas.create_text(
            self.screenshot.width // 2,
            30,
            text=instructions,
            font=('Arial', 16, 'bold'),
            fill='red',
            tags='instructions'
        )

        # Bind mouse events
        self.canvas.bind('<ButtonPress-1>', self.on_mouse_down)
        self.canvas.bind('<B1-Motion>', self.on_mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_mouse_up)
        self.root.bind('<Escape>', lambda e: self.cancel())

        # Start GUI
        self.root.mainloop()

        return self.selected_region

    def on_mouse_down(self, event):
        """Handle mouse button press."""
        self.start_x = event.x
        self.start_y = event.y

        # Delete any existing rectangle
        if self.rect:
            self.canvas.delete(self.rect)

        # Create new rectangle
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='red', width=3
        )

    def on_mouse_drag(self, event):
        """Handle mouse drag."""
        if self.rect:
            # Update rectangle
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_mouse_up(self, event):
        """Handle mouse button release."""
        end_x = event.x
        end_y = event.y

        # Ensure coordinates are in correct order
        left = min(self.start_x, end_x)
        top = min(self.start_y, end_y)
        right = max(self.start_x, end_x)
        bottom = max(self.start_y, end_y)

        # Validate selection size
        width = right - left
        height = bottom - top

        if width < 50 or height < 50:
            messagebox.showerror(
                "Selection Too Small",
                "Please select a larger region (minimum 50x50 pixels)"
            )
            return

        # Confirm selection
        msg = (
            f"Selected region:\n"
            f"Position: ({left}, {top}) to ({right}, {bottom})\n"
            f"Size: {width}x{height} pixels\n\n"
            f"Use this region?"
        )

        if messagebox.askyesno("Confirm Selection", msg):
            self.selected_region = (left, top, right, bottom)
            self.root.quit()
            self.root.destroy()
        else:
            # Reset for another try
            if self.rect:
                self.canvas.delete(self.rect)
                self.rect = None

    def cancel(self):
        """Cancel selection."""
        self.selected_region = None
        self.root.quit()
        self.root.destroy()


def update_config_with_region(region):
    """
    Update config.ini with selected region.

    Args:
        region: (left, top, right, bottom) tuple
    """
    # Find config.ini
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(os.path.dirname(script_dir), 'config.ini')

    # Create config if doesn't exist
    if not os.path.exists(config_path):
        config_example = os.path.join(os.path.dirname(script_dir), 'config.ini.example')
        if os.path.exists(config_example):
            import shutil
            shutil.copy(config_example, config_path)

    # Load config
    config = configparser.ConfigParser()
    config.read(config_path)

    # Ensure sections exist
    if not config.has_section('OCR'):
        config.add_section('OCR')

    # Update region
    left, top, right, bottom = region
    config.set('OCR', 'region_left', str(left))
    config.set('OCR', 'region_top', str(top))
    config.set('OCR', 'region_right', str(right))
    config.set('OCR', 'region_bottom', str(bottom))

    # Save config
    with open(config_path, 'w') as f:
        config.write(f)

    print(f"Configuration updated: {config_path}")
    print(f"Region: ({left}, {top}, {right}, {bottom})")


def main():
    """Run the region selector as standalone tool."""
    print("="*60)
    print("EVE LOCAL MONITOR - Region Selector")
    print("="*60)
    print()
    print("Instructions:")
    print("1. A fullscreen overlay will appear")
    print("2. Click and drag to select your EVE Local player list area")
    print("3. Release mouse to confirm selection")
    print("4. Press ESC to cancel")
    print()
    input("Press Enter to start...")

    selector = RegionSelector()
    region = selector.select_region()

    if region:
        print("\nRegion selected successfully!")
        update_config_with_region(region)
        print("\nYou can now run the monitor:")
        print("  python -m eve_local_monitor.main")
    else:
        print("\nSelection cancelled.")


if __name__ == '__main__':
    main()
