import os
import subprocess
import gi
import threading
import shutil
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib

gi.require_version("Gtk", "3.0")


class UpgradeWindow(Gtk.Window):
    """A separate progress window for updating packages."""

    def __init__(self):
        super().__init__(title="Updating System")
        self.set_default_size(400, 150)
        self.set_resizable(False)
        self.set_border_width(20)
        self.set_name("upgrade_window")

        # Create a VBox layout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.add(vbox)

        # Label for status
        self.label = Gtk.Label(label="Installing updates, please wait...")
        self.label.set_name("upgrade_label")
        vbox.pack_start(self.label, False, False, 5)

        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_size_request(350, 20)
        vbox.pack_start(self.progress_bar, False, False, 5)

        self.show_all()

    def update_progress(self, fraction):
        """Update the progress bar on the upgrade window."""
        self.progress_bar.set_fraction(fraction)

    def close_window(self):
        """Close the upgrade window after the upgrade is complete."""
        self.destroy()


class UpdateWindow(Gtk.Window):
    """Main window for KrenkaOS Update Manager."""

    def __init__(self):
        super().__init__(title="KrenkaOS Update Manager")
        self.set_default_size(600, 350)
        self.set_resizable(False)
        self.set_border_width(10)
        self.set_name("main_window")

        self.load_css()

        self.fixed = Gtk.Fixed()
        self.add(self.fixed)

        self.image = Gtk.Image()
        self.load_tux_image()
        self.fixed.put(self.image, 20, 60)

        # Title label
        self.label_title = Gtk.Label(label="KrenkaOS Update Manager")
        self.label_title.set_name("title_label")
        self.fixed.put(self.label_title, 100, 30)

        # Status label
        self.label_status = Gtk.Label(label="Checking for updates...")
        self.label_status.set_name("status_label")
        self.fixed.put(self.label_status, 150, 80)

        # Update button
        self.button_update = Gtk.Button(label="Check for Updates")
        self.button_update.set_size_request(250, 50)
        self.button_update.set_name("update_button")
        self.button_update.connect("clicked", self.run_update)
        self.fixed.put(self.button_update, 150, 120)

        # Upgrade button
        self.button_upgrade = Gtk.Button(label="Install Updates")
        self.button_upgrade.set_size_request(250, 50)
        self.button_upgrade.set_name("upgrade_button")
        self.button_upgrade.connect("clicked", self.run_upgrade)
        self.fixed.put(self.button_upgrade, 150, 190)

        # Exit button
        self.button_exit = Gtk.Button(label="Exit")
        self.button_exit.set_size_request(250, 50)
        self.button_exit.set_name("exit_button")
        self.button_exit.connect("clicked", Gtk.main_quit)
        self.fixed.put(self.button_exit, 150, 260)

        self.button_about = Gtk.Button(label="About")
        self.button_about.set_size_request(60, 50)
        self.button_about.set_name("about_button")
        self.button_about.connect("clicked", self.show_system_info)
        self.fixed.put(self.button_about, 20, 260)

        self.upgradable_packages = []  # Store package names
        self.check_updates()

    def load_css(self):
        """Load CSS for styling the application."""
        css_provider = Gtk.CssProvider()
        css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "styles.css")

        if os.path.exists(css_path):
            try:
                with open(css_path, "rb") as css_file:
                    css_data = css_file.read()
                    css_provider.load_from_data(css_data)
            except Exception as e:
                print(f"Error loading CSS: {e}")

        display = Gdk.Display.get_default()
        screen = display.get_default_screen()
        Gtk.StyleContext.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def load_tux_image(self):
        """Load and resize the Windows-style logo."""
        image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img/tux.png")

        if os.path.exists(image_path):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(image_path, 100, 100, True)
                self.image.set_from_pixbuf(pixbuf)
            except Exception as e:
                print(f"Error loading image: {e}")

    def run_update(self, widget):
        threading.Thread(target=self.check_updates).start()

    def run_upgrade(self, widget):
        if not self.upgradable_packages:
            self.show_dialog("No updates available", "Your system is already up to date.")
        else:
            threading.Thread(target=self.execute_upgrade).start()

    def check_updates(self):
        """Check for available updates and update the label."""
        try:
            output = subprocess.run(["apt", "list", "--upgradable"], capture_output=True, text=True)
            upgradable_lines = [line for line in output.stdout.split("\n")[1:] if line.strip()]

            self.upgradable_packages = [line.split('/')[0] for line in upgradable_lines]  # Extract package names

            if self.upgradable_packages:
                update_text = f"{len(self.upgradable_packages)} updates available!"
            else:
                update_text = "Your system is up to date."

            GLib.idle_add(self.label_status.set_text, update_text)

        except Exception as e:
            GLib.idle_add(self.label_status.set_text, f"Error checking updates: {e}")

    def execute_upgrade(self):
        """Run upgrade command with a separate window showing progress."""
        upgrade_window = UpgradeWindow()

        upgrade_cmd = ["pkexec", "apt", "upgrade", "-y"] if shutil.which("pkexec") else ["sudo", "apt", "upgrade", "-y"]

        process = subprocess.Popen(
            upgrade_cmd,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        total_steps = 100
        current_step = 0
        upgraded_packages = []  # Track installed packages

        for line in process.stdout:
            if any(keyword in line.lower() for keyword in ["progress", "reading", "preparing", "installing"]):
                current_step += 1
                fraction = min(current_step / total_steps, 1.0)
                GLib.idle_add(upgrade_window.update_progress, fraction)

            # Capture installed package names
            if "Setting up" in line:
                package_name = line.split("Setting up")[-1].strip()
                upgraded_packages.append(package_name)

        GLib.idle_add(upgrade_window.close_window)
        GLib.idle_add(self.show_upgrade_complete_dialog, upgraded_packages)

    def show_dialog(self, title, message):
        """Show a pop-up dialog with a message."""
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=Gtk.DialogFlags.MODAL,
            type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            message_format=message,
        )
        dialog.set_title(title)
        dialog.run()
        dialog.destroy()

    def show_upgrade_complete_dialog(self, upgraded_packages):
        """Show a dialog listing the successfully upgraded packages."""
        if upgraded_packages:
            packages_text = "\n".join(upgraded_packages)
            message = f"System has been successfully updated!\n\nUpgraded packages:\n{packages_text}"
        else:
            message = "System has been successfully updated!"

        self.show_dialog("Upgrade Complete", message)


    def show_system_info(self, widget):
        """Fetch and display full Linux system release information."""
        try:
            # Run `lsb_release -a` to get system details
            result = subprocess.run(["lsb_release", "-a"], capture_output=True, text=True)

            # Format the output
            system_info = result.stdout.strip()
            if not system_info:
                system_info = "System info could not be retrieved."

        except Exception as e:
            system_info = f"Error fetching system info: {e}"

        # Show in a dialog
        self.show_dialog("System Information", system_info)

win = UpdateWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
