import os
import subprocess
import gi
import shutil
import time

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf

class UpdateWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="KrenkaOS Package Manager")
        self.set_default_size(500, 300)
        self.set_resizable(False)
        self.set_border_width(10)

        # Set a name for CSS styling
        self.set_name("main_window")

        # Load CSS
        self.load_css()

        # Create a Fixed layout container
        self.fixed = Gtk.Fixed()
        self.add(self.fixed)

        # Load and display the Tux image
        self.image = Gtk.Image()
        self.load_tux_image()
        self.fixed.put(self.image, 20, 70)  # Position on the left side

        # Title Label
        self.label_title = Gtk.Label(label="KrenkaOS Package Manager")
        self.label_title.set_name("title_label")
        self.fixed.put(self.label_title, 100, 20)

        # Update Button
        self.button_update = Gtk.Button(label="Look for updates")
        self.button_update.set_size_request(200, 50)
        self.button_update.set_name("update_button")
        self.button_update.connect("clicked", self.run_update)
        self.fixed.put(self.button_update, 250, 80)

        # Upgrade Button
        self.button_upgrade = Gtk.Button(label="Install updates")
        self.button_upgrade.set_size_request(200, 50)
        self.button_upgrade.set_name("upgrade_button")
        self.button_upgrade.connect("clicked", self.run_upgrade)
        self.fixed.put(self.button_upgrade, 250, 150)

        # Exit Button
        self.button_exit = Gtk.Button(label="Exit")
        self.button_exit.set_size_request(200, 50)
        self.button_exit.set_name("exit_button")
        self.button_exit.connect("clicked", Gtk.main_quit)
        self.fixed.put(self.button_exit, 250, 220)

    def get_default_terminal(self):
        """Find the user's default terminal emulator."""
        terminals = ["gnome-terminal", "konsole", "xfce4-terminal", "lxterminal", "mate-terminal", "tilix", "alacritty", "terminator", "xterm"]
    
        for terminal in terminals:
            if shutil.which(terminal):  # Check if terminal exists
                return terminal
        return "x-terminal-emulator"  # Fallback for Debian-based systems

    def load_css(self):
        """Load CSS for styling the application."""
        css_provider = Gtk.CssProvider()
        css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "styles.css")

        if os.path.exists(css_path):
            try:
                with open(css_path, "rb") as css_file:
                    css_data = css_file.read()
                    css_provider.load_from_data(css_data)
                    print("CSS Loaded Successfully!")  # Debugging message
            except Exception as e:
                print(f"Error loading CSS: {e}")
        else:
            print(f"Warning: CSS file '{css_path}' not found!")

        display = Gdk.Display.get_default()
        screen = display.get_default_screen()
        Gtk.StyleContext.add_provider_for_screen(
            screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


    def load_tux_image(self):
        """Load and resize the Tux logo."""
        image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img/tux.png")

        if os.path.exists(image_path):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(image_path, 170, 170, True)
                self.image.set_from_pixbuf(pixbuf)
                self.fixed.put(self.image, 35, 70)  # Position on the left side
            except Exception as e:
                print(f"Error loading Tux image: {e}")
        else:
            print(f"Warning: Tux image '{image_path}' not found!")

    def run_update(self, widget):
        """Open the default terminal and run 'sudo apt update'."""
        terminal = self.get_default_terminal()
        process = subprocess.Popen([terminal, "-e", "bash -c 'sudo apt update; exec bash'"])
        self.position_terminal(process)

    def run_upgrade(self, widget):
        """Run 'apt upgrade -y' command."""
        self.execute_command(["pkexec", "apt", "upgrade", "-y"])

    def execute_command(self, command):
        """Execute a system command in a subprocess."""
        try:
            subprocess.Popen(command)
        except Exception as e:
            print(f"Error executing command: {e}")

    def position_terminal(self, process):
        """Move the terminal window to the right side of the screen."""
        # Give the terminal window some time to open
        time.sleep(1)
        # Use wmctrl to move the terminal window to the right side
        subprocess.Popen(["wmctrl", "-r", "Terminal", "-e", "0,1200,100,800,600"])  # Adjust coordinates as necessary

# Launch the GTK application
win = UpdateWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
