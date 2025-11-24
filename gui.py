import dearpygui.dearpygui as dpg
from rfof import Ftx
import datetime
import time


def add_text_to_console(msg) -> None:
    dpg.add_text(msg, parent="console_window")
    dpg.set_y_scroll("console_window", dpg.get_y_scroll_max("console_window"))


class FtxInstance:

    def __init__(self, interface):
        self._interface = interface
        self._ftx = None

    def connect(self):
        try:
            self._ftx = Ftx(self._interface)
        except ValueError:
            add_text_to_console("Could not connect to FTX at interface " + str(self._interface) +
                                ". Check connection and try again.")

    def disconnect(self):
        self._ftx = None

    def set_lna_enable(self, value):
        self._ftx.set_lna_enable(value)

    def get_lna_current(self):
        return self._ftx.get_lna_current()

    def get_lna_voltage(self):
        return self._ftx.get_lna_voltage()

    def set_atten(self, value):
        self._ftx.set_atten(value)

    def get_atten(self):
        return self._ftx.get_atten()

    def set_ld_current(self, value):
        self._ftx.set_ld_current(value)

    def get_ld_current(self):
        return self._ftx.get_ld_current()

    def get_pd_current(self):
        return self._ftx.get_pd_current()

    def get_uid(self):
        return self._ftx.get_uid()

    def get_rf_power(self):
        return self._ftx.get_rf_power()

    def get_temp(self):
        return self._ftx.get_temp()

    def get_vdda_voltage(self):
        return self._ftx.get_vdda_voltage()

    def get_vdd_voltage(self):
        return self._ftx.get_vdd_voltage()


class FtxMon:

    def __init__(self, label, ftx: FtxInstance):
        self.name = label
        self._ftx = ftx
        self.isConnected = False

        with dpg.font_registry():
            default_font = dpg.add_font("fonts/NoName37Light-GW4G.otf", 15)
            bold_font = dpg.add_font("fonts/NoName37-Jl1j.otf", 15)

        with dpg.stage() as self._staging_container_id:
            with dpg.child_window(label=self.name, width=400, height=560):
                self.heading = dpg.add_text(label)  # , pos=[195, 5])
                with dpg.group(horizontal=True):
                    self._connect_button_id = dpg.add_button(label="Connect", callback=self._connect)  # ,
                                                             # pos=[180, 30])
                    self._disconnect_button_id = dpg.add_button(label="Disconnect", callback=self._disconnect,
                                                                show=False)  # , pos=[180, 30])
                l1 = dpg.add_text("LNA Bias Enable", color=(37, 37, 37))
                self._lna_bias_checkbox_id = dpg.add_checkbox(label="", enabled=False, callback=self._lna_bias_checked)
                dpg.add_spacer()
                with dpg.group(horizontal=True, horizontal_spacing=100):
                    with dpg.group():
                        l2 = dpg.add_text("LNA Current (mA)", color=(37, 37, 37))
                        self._lna_current_id = dpg.add_text("0.0", color=(69, 69, 69))
                    with dpg.group():
                        l3 = dpg.add_text("LNA Voltage (V)", color=(37, 37, 37))
                        self._lna_voltage_id = dpg.add_text("0.0", color=(69, 69, 69))
                dpg.add_spacer()
                l4 = dpg.add_text("RF Monitor (dBm)", color=(37, 37, 37))
                self._rfmon_id = dpg.add_text("0.0", color=(69, 69, 69))
                dpg.add_spacer()
                with dpg.group(horizontal=True, horizontal_spacing=50):
                    with dpg.group():
                        l5 = dpg.add_text("Input Attenuation (dB)", color=(37, 37, 37))
                        self._attn_id = dpg.add_text(default_value="0.0", color=(69, 69, 69))
                    with dpg.group():
                        l7 = dpg.add_text("Control", color=(37, 37, 37))
                        self._input_attn_id = dpg.add_input_float(enabled=False, default_value=0,
                                                                  max_value=31.25, min_value=0, step=0.25,
                                                                  callback=self._update_attn, on_enter=True, width=150,
                                                                  min_clamped=True, max_clamped=True, format='%.2f')
                dpg.add_spacer()
                with dpg.group(horizontal=True, horizontal_spacing=75):
                    with dpg.group():
                        l8 = dpg.add_text("Laser Current (mA)", color=(37, 37, 37))
                        self._laser_current_id = dpg.add_text("0.0", color=(69, 69, 69))
                    with dpg.group():
                        l9 = dpg.add_text(" ")
                        self._laser_current_input_id = dpg.add_input_float(enabled=False, default_value=25,
                                                                           max_value=50, min_value=0, step=0.25,
                                                                           callback=self._update_laser, on_enter=True,
                                                                           min_clamped=True, max_clamped=True,
                                                                           format='%.2f', width=150)
                dpg.add_spacer()
                l10 = dpg.add_text("Photodiode Current (uA)", color=(37, 37, 37))
                self._laserpd_mon_id = dpg.add_text("0.0", color=(69, 69, 69))
                dpg.add_spacer()
                l11 = dpg.add_text("Serial Number", color=(37, 37, 37))
                self._sn_id = dpg.add_text("0000", color=(69, 69, 69))
                dpg.add_spacer()
                l12 = dpg.add_text("Temperature", color=(37, 37, 37))
                self._temp_id = dpg.add_text("0.0", color=(69, 69, 69))
                dpg.add_spacer()
                with dpg.group(horizontal=True, horizontal_spacing=100):
                    with dpg.group():
                        l13 = dpg.add_text("Vdd Voltage (V)", color=(37, 37, 37))
                        self._vdd_id = dpg.add_text("0.0", color=(69, 69, 69))
                    with dpg.group():
                        l14 = dpg.add_text("Vdda Voltage (V)", color=(37, 37, 37))
                        self._vdda_id = dpg.add_text("0.0", color=(69, 69, 69))
                dpg.add_spacer()

                dpg.bind_font(default_font)
                dpg.bind_item_font(l1, bold_font)
                dpg.bind_item_font(l2, bold_font)
                dpg.bind_item_font(l3, bold_font)
                dpg.bind_item_font(l4, bold_font)
                dpg.bind_item_font(l5, bold_font)
                dpg.bind_item_font(l7, bold_font)
                dpg.bind_item_font(l8, bold_font)
                dpg.bind_item_font(l9, bold_font)
                dpg.bind_item_font(l10, bold_font)
                dpg.bind_item_font(l11, bold_font)
                dpg.bind_item_font(l12, bold_font)
                dpg.bind_item_font(l13, bold_font)
                dpg.bind_item_font(l14, bold_font)

    def _connect(self):
        self._ftx.connect()
        self.isConnected = True
        dpg.configure_item(self._connect_button_id, show=False)
        dpg.configure_item(self._disconnect_button_id, show=True)

        add_text_to_console("Connected to " + self.name + ". Control fields are now enabled.")

        dpg.configure_item(self._lna_bias_checkbox_id, enabled=True)
        dpg.configure_item(self._input_attn_id, enabled=True)
        dpg.configure_item(self._laser_current_input_id, enabled=True)

        dpg.configure_item(self._lna_current_id, color=(255, 255, 255))
        dpg.configure_item(self._laser_current_id, color=(255, 255, 255))
        dpg.configure_item(self._vdda_id, color=(255, 255, 255))
        dpg.configure_item(self._vdd_id, color=(255, 255, 255))
        dpg.configure_item(self._lna_voltage_id, color=(255, 255, 255))
        dpg.configure_item(self._sn_id, color=(255, 255, 255))
        dpg.configure_item(self._rfmon_id, color=(255, 255, 255))
        dpg.configure_item(self._laserpd_mon_id, color=(255, 255, 255))
        dpg.configure_item(self._temp_id, color=(255, 255, 255))
        dpg.configure_item(self._attn_id, color=(255, 255, 255))

        self.update_mon()

    def _disconnect(self):
        self._ftx.disconnect()
        self.isConnected = False
        dpg.configure_item(self._connect_button_id, show=True)
        dpg.configure_item(self._disconnect_button_id, show=False)

        add_text_to_console(self.name + " board connection closed. OK to unplug.")

        # Disable all the settings inputs
        dpg.configure_item(self._lna_bias_checkbox_id, enabled=False)
        dpg.configure_item(self._input_attn_id, enabled=False)
        dpg.configure_item(self._laser_current_input_id, enabled=False)

        dpg.configure_item(self._sn_id, color=(37, 37, 37))
        dpg.configure_item(self._rfmon_id, color=(37, 37, 37))
        dpg.configure_item(self._lna_current_id, color=(37, 37, 37))
        dpg.configure_item(self._laser_current_id, color=(37, 37, 37))
        dpg.configure_item(self._laserpd_mon_id, color=(37, 37, 37))
        dpg.configure_item(self._temp_id, color=(37, 37, 37))
        dpg.configure_item(self._vdda_id, color=(37, 37, 37))
        dpg.configure_item(self._vdd_id, color=(37, 37, 37))
        dpg.configure_item(self._attn_id, color=(37, 37, 37))
        dpg.configure_item(self._lna_voltage_id, color=(37, 37, 37))

    def _lna_bias_checked(self, sender) -> None:
        """ Callback for when the lna bias enable checkbox is clicked.

        If turned on, sends the lna bias enable command
        If turned off, sends the lna bias disable command
        """
        value = dpg.get_value(sender)
        self._ftx.set_lna_enable(value)
        if value:
            add_text_to_console("LNA bias enabled.")
            dpg.configure_item(self._lna_current_id, color=(255, 255, 255))
            dpg.configure_item(self._lna_voltage_id, color=(255, 255, 255))
            try:
                dpg.set_value(self._lna_current_id, "{:.4f}".format(self._ftx.get_lna_current()))
                dpg.set_value(self._lna_voltage_id, "{:.4f}".format(self._ftx.get_lna_voltage()))
            except TimeoutError:
                add_text_to_console("Timeout while reading LNA current and voltage.")
        else:
            add_text_to_console("LNA bias disabled.")
            dpg.configure_item(self._lna_current_id, color=(37, 37, 37))
            dpg.configure_item(self._lna_voltage_id, color=(37, 37, 37))

    def _update_attn(self, sender) -> None:
        new_value = dpg.get_value(self._input_attn_id)
        self._ftx.set_atten(new_value)
        add_text_to_console("Setting input attenuation to " + str(new_value) + "...")
        time.sleep(0.1)
        try:
            set_value = self._ftx.get_atten()
            dpg.set_value(self._attn_id, set_value)
            if new_value != set_value:
                add_text_to_console(
                    "**WARNING** Value input: " + str(round(new_value, 2)) + ", value set: " + str(set_value) + ".")
        except TimeoutError:
            add_text_to_console("Timeout while reading FTX attenuation value.")

    def _update_laser(self) -> None:
        new_value = dpg.get_value(self._laser_current_input_id)
        self._ftx.set_ld_current(new_value)
        add_text_to_console("Setting laser current to " + str(new_value) + "...")
        time.sleep(0.1)
        try:
            set_value = self._ftx.get_ld_current()
            dpg.set_value(self._laser_current_id, set_value)
            if new_value != set_value:
                add_text_to_console("**WARNING** Value input: "+str(round(new_value, 2))+", value set: "+str(set_value)+".")
        except TimeoutError:
            add_text_to_console("Timeout while reading Laser Diode current.")

    def update_mon(self):
        try:
            dpg.set_value(self._lna_current_id, "{:.4f}".format(self._ftx.get_lna_current()))
            dpg.set_value(self._lna_voltage_id, "{:.4f}".format(self._ftx.get_lna_voltage()))
            dpg.set_value(self._laser_current_id, "{:.4f}".format(self._ftx.get_ld_current()))
            dpg.set_value(self._laserpd_mon_id, "{:.4f}".format(self._ftx.get_pd_current()))
            dpg.set_value(self._sn_id, self._ftx.get_uid())
            dpg.set_value(self._rfmon_id, "{:.4f}".format(self._ftx.get_rf_power()))
            dpg.set_value(self._attn_id, "{:.4f}".format(self._ftx.get_atten()))
            dpg.set_value(self._temp_id, "{:.4f}".format(self._ftx.get_temp()))
            dpg.set_value(self._vdda_id, "{:.4f}".format(self._ftx.get_vdda_voltage()))
            dpg.set_value(self._vdd_id, "{:.4f}".format(self._ftx.get_vdd_voltage()))
        except RuntimeError:
            add_text_to_console("Timeout while reading FTX monitor values.")

    def get_temp(self):
        return dpg.get_value(self._temp_id)

    def submit(self, parent):
        dpg.push_container_stack(parent)
        dpg.unstage(self._staging_container_id)
        dpg.pop_container_stack()


class UserInterface:
    VID = 0x0403
    PID = 0x6048

    def __init__(self):
        self.fi = open('C:\\Users\\ckeeler\\Desktop\\temp_data' + datetime.datetime.now().strftime("%m%d_%H%M%S") +
                       '.csv', 'w')

        dpg.create_context()

        self.windowA = FtxMon("FTX-A", FtxInstance(1))
        self.windowB = FtxMon("FTX-B", FtxInstance(0))

        dpg.create_viewport(title='USB-I2C Control Program', width=845, height=630)
        dpg.setup_dearpygui()
        dpg.set_exit_callback(self._exit_callback)
        self._make_gui()
        dpg.set_primary_window("primary_window", True)
        dpg.show_viewport()
        dpg.set_viewport_resizable(False)
        ti = dpg.get_total_time()
        while dpg.is_dearpygui_running():
            tf = dpg.get_total_time()
            if (tf - ti) > 2:  # approx 2 second intervals
                ti = tf
                self._timer_callback()
            dpg.render_dearpygui_frame()
        dpg.destroy_context()

    def _timer_callback(self) -> None:
        """Timer callback that runs approx every 2 second.

        If any ftx is connected, this will refresh the
        monitor data"""
        string = datetime.datetime.now().strftime("%d/%m/%y %H:%M:%S") + ","
        if self.windowA.isConnected:
            self.windowA.update_mon()
            string = string + self.windowA.get_temp() + ","
        else:
            string = string + ","

        if self.windowB.isConnected:
            self.windowB.update_mon()
            string = string + self.windowB.get_temp() + "\n"
        else:
            string = string + "\n"

        self.fi.write(string)

    def _exit_callback(self) -> None:
        """Exit callback when the application is closed.

        Call the exit , function on the csv file to
        ensure we terminate the session properly.
        """
        self.fi.close()

    def _make_gui(self) -> None:
        """Create the layout for the entire application."""
        with dpg.font_registry():
            # first argument ids the path to the .ttf or .otf file
            default_font = dpg.add_font("fonts/NoName37Light-GW4G.otf", 15)
            second_font = dpg.add_font("fonts/NoName37Light-GW4G.otf", 20)
            console_font = dpg.add_font("fonts/NoName37Light-GW4G.otf", 12)

        with dpg.window(label="USB-I2C Control Program", tag="primary_window") as main:

            with dpg.group(label="overall", horizontal=True) as thing:
                self.windowA.submit(thing)
                self.windowB.submit(thing)

            with dpg.child_window(tag="console_window", width=810, height=110) as win1:
                dpg.add_text("Welcome to the console.")
                dpg.add_text("Connect to the RF over Fiber boards to begin.")

        dpg.bind_font(default_font)
        dpg.bind_item_font(self.windowA.heading, second_font)
        dpg.bind_item_font(self.windowB.heading, second_font)

        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (255, 140, 23), category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, (69, 69, 69), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (44, 44, 44), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (69, 69, 69), category=dpg.mvThemeCat_Core)

            # Input box background color + frame
            with dpg.theme_component(dpg.mvInputInt):
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (155, 250, 65), category=dpg.mvThemeCat_Core)  # GRB
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)

        dpg.bind_item_theme(main, global_theme)

        with dpg.theme() as console_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (37, 37, 37), category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)

        dpg.bind_item_theme(win1, console_theme)
        dpg.bind_item_font(win1, console_font)

        # dpg.show_style_editor()
