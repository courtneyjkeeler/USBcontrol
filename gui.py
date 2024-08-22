import dearpygui.dearpygui as dpg
from pyftdi.i2c import I2cController, I2cIOError, I2cTimeoutError
from rfof import Ftx
from rfof import Frx
import usb.core
import usb.util
import time


def add_text_to_console(msg) -> None:
    dpg.add_text(msg, parent="console_window")
    dpg.set_y_scroll("console_window", dpg.get_y_scroll_max("console_window"))


class UserInterface:
    VID = 0x0403
    PID = 0x6048

    def __init__(self):
        self.ftx = None
        self.frx = None
        self.i2c_receive = None
        self.i2c_transmit = None
        self._lna_current_id = 0
        self._lna_voltage_id = 0
        self._laser_current_id = 0
        self._laserpd_mon_id = 0
        self._ftx_sn_id = 0
        self._ftx_rfmon_id = 0
        self._ftx_attn_id = 0
        self._ftx_temp_id = 0
        self._ftx_vdd_id = 0
        self._ftx_vdda_id = 0
        self._frx_rfmon_id = 0
        self._pd_current_id = 0
        self._frx_sn_id = 0
        self._temp_id = 0
        self._frx_attn_id = 0
        self.comments = ""
        self.opt_attn = "None"

        dpg.create_context()
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

        If the frx or ftx is connected, this will refresh the
        monitor data"""
        if self.frx is not None:
            self._update_mon_frx()

        if self.ftx is not None:
            self._update_mon_ftx()

    def _exit_callback(self) -> None:
        """Exit callback when the application is closed.

        If there is a running connection to the machine, call the exit function on the SA to
        ensure we terminate the session properly.
        """
        if self.frx is not None:
            add_text_to_console("Disconnecting from FRX board...")
            self.i2c_receive.close()
        if self.ftx is not None:
            add_text_to_console("Disconnecting from FTX board...")
            self.i2c_transmit.close()

    def save_data(self, file_path):
        # TODO: update for new monitor fields
        add_text_to_console("Saving data to .csv file...")
        with open(file_path, 'w') as f:
            f.write('Date,' + time.strftime("%m/%d/%Y", time.localtime()) + '\n')
            f.write('Time,' + time.strftime("%H:%M:%S", time.localtime()) + '\n')
            f.write('Optical Attenuation,' + self.opt_attn + '\n')
            f.write('Comments,' + self.comments + '\n')
            f.write('\n')
            f.write('FTX, Value, Units, Mon/Cmd\n')
            if dpg.get_value("lna_bias_checkbox"):
                msg = 'ON'
            else:
                msg = 'OFF'
            f.write('LNA Bias Enable,'+msg+',,Cmd\n')
            if dpg.get_value("lna_bias_checkbox"):
                f.write('LNA Current,'+dpg.get_value(self._lna_current_id)+',mA,Mon\n')
            else:
                f.write('LNA Current,N/A,mA,Mon\n')
            f.write('RF Monitor,'+dpg.get_value(self._ftx_rfmon_id)+',dBm,Mon\n')
            f.write('Input Attenuation,' + str(dpg.get_value("ftx_input_attn")) + ',dB,Cmd\n')
            f.write('Laser Current,' + str(dpg.get_value("ftx_laser_current")) + ',mA,Cmd\n')
            f.write('PD Current,' + dpg.get_value(self._laserpd_mon_id) + ',mA,Mon\n')
            f.write('FTX SN,' + dpg.get_value(self._ftx_sn_id) + ',,Mon\n')
            f.write('\n')
            f.write('FRX\n')
            f.write('PD Current,' + dpg.get_value(self._pd_current_id) + ',mA,Mon\n')
            f.write('RF Monitor,' + dpg.get_value(self._frx_rfmon_id) + ',dBm,Mon\n')
            f.write('Output Attenuation,' + str(dpg.get_value("frx_output_attn")) + ',dB,Cmd\n')
            f.write('Temperature,' + dpg.get_value(self._temp_id) + ',degC,Mon\n')
            f.write('FRX SN,' + dpg.get_value(self._frx_sn_id) + ',,Mon\n')
        add_text_to_console("Done.")

    def _connect_frx(self, sender=None, data=None) -> None:
        """Callback for clicking the connect button.

        Calls the configure function on the I2C ports.
        """
        self.i2c_receive = I2cController()
        dev = usb.core.find(idVendor=0x0403, idProduct=0x6048)
        # dev = usb.core.find(idVendor=1027, idProduct=24592)  # Tigard
        if dev is None:
            add_text_to_console('USB Device not found!')
            return
        try:
            self.i2c_receive.configure(dev, interface=1)
            # self.i2c_receive.configure(dev, interface=2)
            self.frx = Frx(self.i2c_receive)
        except I2cIOError:
            # Log the error to the console
            add_text_to_console("Could not connect to FRX board, check connection and try again.")
            return

        add_text_to_console("Connected to the FRX board. Control fields are now enabled.")

        dpg.configure_item("frx_connect_button", show=False)
        dpg.configure_item("frx_disconnect_button", show=True)
        # Enable all the control inputs
        dpg.configure_item("frx_output_attn", enabled=True)

        dpg.configure_item(self._frx_sn_id, color=(255, 255, 255))
        dpg.configure_item(self._frx_rfmon_id, color=(255, 255, 255))
        dpg.configure_item(self._pd_current_id, color=(255, 255, 255))
        dpg.configure_item(self._temp_id, color=(255, 255, 255))
        dpg.configure_item(self._frx_attn_id, color=(255, 255, 255))

        self._update_mon_frx()

    def _save_callback(self, sender, app_data) -> None:
        self.save_data(app_data.get('file_path_name'))

    def _connect_ftx(self, sender=None, data=None) -> None:
        """Callback for clicking the connect button.

        Calls the configure function on the I2C ports.
        """

        dev = usb.core.find(idVendor=0x0403, idProduct=0x6048)  # Custom
        # dev = usb.core.find(idVendor=1027, idProduct=24592)  # Tigard
        if dev is None:
            add_text_to_console("Could not find the USB device, check connection and try again.")
            return

        self.i2c_transmit = I2cController()
        try:
            self.i2c_transmit.configure(dev, interface=2)
            self.ftx = Ftx(self.i2c_transmit)
        except I2cIOError:
            # Log the error to the console
            add_text_to_console("Could not connect to FTX board, check connection and try again.")
            return

        add_text_to_console("Connected to the FTX board. Control fields are now enabled.")
        dpg.configure_item("ftx_connect_button", show=False)
        dpg.configure_item("ftx_disconnect_button", show=True)
        # Enable all the control inputs
        dpg.configure_item("lna_bias_checkbox", enabled=True)
        dpg.configure_item("ftx_input_attn", enabled=True)
        dpg.configure_item("ftx_laser_current", enabled=True)

        dpg.configure_item(self._ftx_sn_id, color=(255, 255, 255))
        dpg.configure_item(self._ftx_rfmon_id, color=(255, 255, 255))
        # dpg.configure_item(self._lna_current_id, color=(255, 255, 255))
        dpg.configure_item(self._laser_current_id, color=(255, 255, 255))
        dpg.configure_item(self._laserpd_mon_id, color=(255, 255, 255))
        dpg.configure_item(self._ftx_temp_id, color=(255, 255, 255))
        dpg.configure_item(self._ftx_vdda_id, color=(255, 255, 255))
        dpg.configure_item(self._ftx_vdd_id, color=(255, 255, 255))
        dpg.configure_item(self._ftx_attn_id, color=(255, 255, 255))
        # dpg.configure_item(self._lna_voltage_id, color=(255, 255, 255))

        self._update_mon_ftx()

    def _disconnect_ftx(self, sender=None, data=None) -> None:
        """Callback for clicking the disconnect button.

        Calls the disconnect function on the SA to terminate the session.
        """
        dpg.configure_item("ftx_connect_button", show=True)
        dpg.configure_item("ftx_disconnect_button", show=False)
        self.i2c_transmit.close()
        add_text_to_console("FTX board connection closed. OK to unplug.")
        self.ftx = None
        # Disable all the settings inputs
        dpg.configure_item("lna_bias_checkbox", enabled=False)
        dpg.configure_item("ftx_input_attn", enabled=False)
        dpg.configure_item("ftx_laser_current", enabled=False)
        dpg.configure_item(self._ftx_sn_id, color=(37, 37, 37))
        dpg.configure_item(self._ftx_rfmon_id, color=(37, 37, 37))
        dpg.configure_item(self._lna_current_id, color=(37, 37, 37))
        dpg.configure_item(self._laser_current_id, color=(37, 37, 37))
        dpg.configure_item(self._laserpd_mon_id, color=(37, 37, 37))
        dpg.configure_item(self._ftx_temp_id, color=(37, 37, 37))
        dpg.configure_item(self._ftx_vdda_id, color=(37, 37, 37))
        dpg.configure_item(self._ftx_vdd_id, color=(37, 37, 37))
        dpg.configure_item(self._ftx_attn_id, color=(37, 37, 37))
        dpg.configure_item(self._lna_voltage_id, color=(37, 37, 37))

    def _disconnect_frx(self, sender=None, data=None) -> None:
        """Callback for clicking the disconnect button.

        Calls the disconnect function on the SA to terminate the session.
        """
        dpg.configure_item("frx_connect_button", show=True)
        dpg.configure_item("frx_disconnect_button", show=False)
        self.i2c_receive.close()
        self.frx = None
        # Disable all the settings inputs
        dpg.configure_item("frx_output_attn", enabled=False)
        dpg.configure_item(self._frx_sn_id, color=(37, 37, 37))
        dpg.configure_item(self._frx_rfmon_id, color=(37, 37, 37))
        dpg.configure_item(self._pd_current_id, color=(37, 37, 37))
        dpg.configure_item(self._temp_id, color=(37, 37, 37))
        dpg.configure_item(self._frx_attn_id, color=(37, 37, 37))

    def _show_popup_window(self, sender=None, data=None, user_data=None) -> None:
        """Callback for when certain buttons are clicked.

        Displays a small popup window with a message and button to indicate users are
        ready.
        """
        message = user_data.get("msg", None)
        if message is None:
            return
        if dpg.does_item_exist("blocking_popup"):
            dpg.configure_item("blocking_popup", width=150, height=50,
                               pos=((dpg.get_viewport_width() - 150) // 2, (dpg.get_viewport_height() - 50) // 2))
            dpg.configure_item("blocking_popup", show=True)
            dpg.set_value("blocking_popup_text", message)
            dpg.set_item_user_data("blocking_popup_button", user_data)
            return
        with dpg.window(tag="blocking_popup", width=150, height=50,
                        pos=((dpg.get_viewport_width() - 150) // 2, (dpg.get_viewport_height() - 50) // 2)):
            dpg.add_text(message, tag="blocking_popup_text")
            dpg.add_input_text(multiline=True, tag='multiline_input')
            dpg.add_button(label="OK", tag="blocking_popup_button", user_data=user_data,
                           callback=self._save_comments)

    def _save_comments(self, sender=None, data=None, user_data=None) -> None:
        message = user_data.get("msg", None)
        if message == "Add comments below:":
            self.comments = dpg.get_value('multiline_input')
        else:
            self.opt_attn = dpg.get_value('multiline_input')
        dpg.delete_item('blocking_popup')

    def _lna_bias_checked(self, sender) -> None:
        """ Callback for when the lna bias enable checkbox is clicked.

        If turned on, sends the lna bias enable command
        If turned off, sends the lna bias disable command
        """
        value = dpg.get_value(sender)
        self.ftx.set_lna_enable(value)
        if value:
            add_text_to_console("LNA bias enabled.")
            dpg.configure_item(self._lna_current_id, color=(255, 255, 255))
            dpg.configure_item(self._lna_voltage_id, color=(255, 255, 255))
            try:
                dpg.set_value(self._lna_current_id, "{:.2f}".format(self.ftx.get_lna_current()))
                dpg.set_value(self._lna_voltage_id, "{:.2f}".format(self.ftx.get_lna_voltage()))
            except TimeoutError:
                add_text_to_console("Timeout while reading LNA current and voltage.")
        else:
            add_text_to_console("LNA bias disabled.")
            dpg.configure_item(self._lna_current_id, color=(37, 37, 37))
            dpg.configure_item(self._lna_voltage_id, color=(37, 37, 37))

    def _update_ftx_attn(self) -> None:
        new_value = dpg.get_value("ftx_input_attn")
        self.ftx.set_atten(new_value)
        add_text_to_console("Setting input attenuation to " + str(new_value) + "...")
        time.sleep(0.1)
        try:
            set_value = self.ftx.get_atten()
            dpg.set_value("ftx_attn", set_value)
            if new_value != set_value:
                add_text_to_console(
                    "**WARNING** Value input: " + str(round(new_value, 2)) + ", value set: " + str(set_value) + ".")
        except TimeoutError:
            add_text_to_console("Timeout while reading FTX attenuation value.")

    def _update_ftx_laser(self) -> None:
        new_value = dpg.get_value("ftx_laser_current")
        self.ftx.set_ld_current(new_value)
        add_text_to_console("Setting laser current to " + str(new_value) + "...")
        time.sleep(0.1)
        try:
            set_value = self.ftx.get_ld_current()
            dpg.set_value("ftx_laser_current_mon", set_value)
            if new_value != set_value:
                add_text_to_console("**WARNING** Value input: "+str(round(new_value, 2))+", value set: "+str(set_value)+".")
        except TimeoutError:
            add_text_to_console("Timeout while reading Laser Diode current.")

    def _update_frx_attn(self) -> None:
        new_value = dpg.get_value("frx_output_attn")
        self.frx.set_atten(new_value)
        add_text_to_console("Setting output attenuation to " + str(new_value) + "...")
        time.sleep(0.1)
        try:
            set_value = self.frx.get_atten()
            dpg.set_value(self._frx_attn_id, set_value)
            if new_value != set_value:
                add_text_to_console("**WARNING** Value input: " + str(round(new_value, 2)) + ", value set: " +
                                    str(set_value) + ".")
        except TimeoutError:
            add_text_to_console("Timeout while reading FRX attenuation value.")

    def _update_mon_frx(self) -> None:
        """ Reads all the monitor data and updates the
            display accordingly. Called every 2 seconds.
        """
        try:
            dpg.set_value(self._frx_rfmon_id, "{:.2f}".format(self.frx.get_rf_power()))
            dpg.set_value(self._pd_current_id, "{:.2f}".format(self.frx.get_pd_current()))
            dpg.set_value(self._frx_sn_id, self.frx.get_uid())
            dpg.set_value(self._temp_id, "{:.2f}".format(self.frx.get_temp()))
            dpg.set_value(self._frx_attn_id, "{:.2f}".format(self.frx.get_atten()))
        except TimeoutError:
            add_text_to_console("Timeout while updating FRX monitor values.")

    def _update_mon_ftx(self) -> None:
        """ Reads all the monitor data and updates the
            display accordingly
        """
        try:
            if dpg.get_value("lna_bias_checkbox"):
                dpg.set_value(self._lna_current_id, "{:.2f}".format(self.ftx.get_lna_current()))
                dpg.set_value(self._lna_voltage_id, "{:.2f}".format(self.ftx.get_lna_voltage()))
            dpg.set_value(self._laser_current_id, "{:.2f}".format(self.ftx.get_ld_current()))
            dpg.set_value(self._laserpd_mon_id, "{:.2f}".format(self.ftx.get_pd_current()))
            dpg.set_value(self._ftx_sn_id, self.ftx.get_uid())
            dpg.set_value(self._ftx_rfmon_id, "{:.2f}".format(self.ftx.get_rf_power()))
            dpg.set_value(self._ftx_attn_id, "{:.2f}".format(self.ftx.get_atten()))
            dpg.set_value(self._ftx_temp_id, "{:.2f}".format(self.ftx.get_temp()))
            dpg.set_value(self._ftx_vdda_id, "{:.2f}".format(self.ftx.get_vdda_voltage()))
            dpg.set_value(self._ftx_vdd_id, "{:.2f}".format(self.ftx.get_vdd_voltage()))
        except TimeoutError:
            add_text_to_console("Timeout while reading FTX monitor values.")

    def _make_gui(self) -> None:
        """Create the layout for the entire application."""
        with dpg.font_registry():
            # first argument ids the path to the .ttf or .otf file
            default_font = dpg.add_font("fonts/NoName37Light-GW4G.otf", 15)
            second_font = dpg.add_font("fonts/NoName37Light-GW4G.otf", 20)
            console_font = dpg.add_font("fonts/NoName37Light-GW4G.otf", 12)
            bold_font = dpg.add_font("fonts/NoName37-Jl1j.otf", 15)

        with dpg.file_dialog(directory_selector=False, show=False, callback=self._save_callback,
                             tag="save_as_dialog_id", width=700, height=400):
            dpg.add_file_extension(".csv", color=(0, 255, 0, 255), custom_text="[CSV]")

        with dpg.window(label="USB-I2C Control Program", tag="primary_window") as main:
            with dpg.menu_bar():
                with dpg.menu(label="File"):
                    dpg.add_menu_item(label="Save Data", callback=lambda: dpg.show_item("save_as_dialog_id"))

                    with dpg.menu(label="Add..."):
                        dpg.add_menu_item(label="Optical Attn", callback=self._show_popup_window, check=True,
                                          user_data={'msg': "Enter the optical attenuation in dB:"})
                        dpg.add_menu_item(label="Comments", callback=self._show_popup_window,
                                          user_data={'msg': "Add comments below:"})

            with dpg.group(label="overall", horizontal=True):
                with dpg.group(label="left_side"):
                    with dpg.child_window(tag="FTX", width=400, height=550) as ftx_win:
                        with dpg.group(tag="ftx_settings_group"):
                            h1 = dpg.add_text("FTX", pos=[195, 5])
                            with dpg.group(tag="ftx_connect_buttons_group", horizontal=True):
                                dpg.add_button(label="Connect", tag="ftx_connect_button", callback=self._connect_ftx,
                                               pos=[180, 30])
                                dpg.add_button(label="Disconnect", tag="ftx_disconnect_button",
                                               callback=self._disconnect_ftx, show=False, pos=[180, 30])
                            t1 = dpg.add_text("LNA Bias Enable", color=(37, 37, 37))
                            dpg.add_checkbox(label="", tag="lna_bias_checkbox", enabled=False,
                                             callback=self._lna_bias_checked)
                            dpg.add_spacer()
                            with dpg.group(horizontal=True, horizontal_spacing=100):
                                with dpg.group():
                                    t2 = dpg.add_text("LNA Current (mA)", color=(37, 37, 37))
                                    self._lna_current_id = dpg.add_text("0.0", tag="ftx_lna_current", color=(69, 69, 69))
                                with dpg.group():
                                    t22 = dpg.add_text("LNA Voltage (V)", color=(37, 37, 37))
                                    self._lna_voltage_id = dpg.add_text("0.0", tag="ftx_lna_voltage", color=(69, 69, 69))
                            dpg.add_spacer()
                            t3 = dpg.add_text("RF Monitor (dBm)", color=(37, 37, 37))
                            self._ftx_rfmon_id = dpg.add_text("0.0", tag="ftx_rf_mon", color=(69, 69, 69))
                            dpg.add_spacer()
                            with dpg.group(horizontal=True, horizontal_spacing=50):
                                with dpg.group():
                                    t4 = dpg.add_text("Input Attenuation (dB)", color=(37, 37, 37))
                                    self._ftx_attn_id = dpg.add_text(default_value="0.0", tag="ftx_attn", color=(69, 69, 69))
                                with dpg.group():
                                    dpg.add_text("Control", color=(37, 37, 37))
                                    dpg.add_input_float(tag="ftx_input_attn", enabled=False, default_value=0,
                                                        max_value=31.25,
                                                        min_value=0, step=0.25, callback=self._update_ftx_attn,
                                                        on_enter=True, width=150,
                                                        min_clamped=True, max_clamped=True, format='%.2f')
                            dpg.add_spacer()
                            with dpg.group(horizontal=True, horizontal_spacing=75):
                                with dpg.group():
                                    t5 = dpg.add_text("Laser Current (mA)", color=(37, 37, 37))
                                    self._laser_current_id = dpg.add_text("0.0", tag="ftx_laser_current_mon", color=(69, 69, 69))
                                with dpg.group():
                                    dpg.add_text(" ")
                                    dpg.add_input_float(tag="ftx_laser_current", enabled=False, default_value=25,
                                                        max_value=50, min_value=0, step=0.25, callback=self._update_ftx_laser,
                                                        on_enter=True, min_clamped=True, max_clamped=True, format='%.2f',
                                                        width=150)
                            dpg.add_spacer()
                            t6 = dpg.add_text("Photodiode Current (uA)", color=(37, 37, 37))
                            self._laserpd_mon_id = dpg.add_text("0.0", tag="ftx_laserpd_mon", color=(69, 69, 69))
                            dpg.add_spacer()
                            t7 = dpg.add_text("Serial Number", color=(37, 37, 37))
                            self._ftx_sn_id = dpg.add_text("0000", tag="ftx_sn", color=(69, 69, 69))
                            dpg.add_spacer()
                            t13 = dpg.add_text("Temperature", color=(37, 37, 37))
                            self._ftx_temp_id = dpg.add_text("0.0", tag="ftx_temp", color=(69, 69, 69))
                            dpg.add_spacer()
                            with dpg.group(horizontal=True, horizontal_spacing=100):
                                with dpg.group():
                                    t14 = dpg.add_text("Vdd Voltage (V)", color=(37, 37, 37))
                                    self._ftx_vdd_id = dpg.add_text("0.0", tag="ftx_vdd", color=(69, 69, 69))
                                with dpg.group():
                                    t15 = dpg.add_text("Vdda Voltage (V)", color=(37, 37, 37))
                                    self._ftx_vdda_id = dpg.add_text("0.0", tag="ftx_vdda", color=(69, 69, 69))
                            dpg.add_spacer()
                with dpg.group(label="right_side"):
                    with dpg.child_window(tag="FRX", width=400, height=550) as frx_win:
                        with dpg.group(tag="frx_settings_group"):
                            h2 = dpg.add_text("FRX", pos=[195, 5])
                            with dpg.group(tag="frx_connect_buttons_group", horizontal=True):
                                dpg.add_button(label="Connect", tag="frx_connect_button", callback=self._connect_frx,
                                               pos=[180, 30])
                                dpg.add_button(label="Disconnect", tag="frx_disconnect_button",
                                               callback=self._disconnect_frx, show=False, pos=[180, 30])
                            t8 = dpg.add_text("Photodiode Current (mA)", color=(37, 37, 37))
                            self._pd_current_id = dpg.add_text("0.0", tag="frx_pd_current", color=(69, 69, 69))
                            dpg.add_spacer()
                            t9 = dpg.add_text("RF Monitor (dBm)", color=(37, 37, 37))
                            self._frx_rfmon_id = dpg.add_text("0.0", tag="frx_rf_mon", color=(69, 69, 69))
                            dpg.add_spacer()
                            with dpg.group(horizontal=True, horizontal_spacing=50):
                                with dpg.group():
                                    t10 = dpg.add_text("Output Attenuation (dB)", color=(37, 37, 37))
                                    self._frx_attn_id = dpg.add_text("0.0", tag="frx_attn_mon", color=(69, 69, 69))
                                with dpg.group():
                                    dpg.add_text("Control", color=(37, 37, 37))
                                    dpg.add_input_float(tag="frx_output_attn", enabled=False, default_value=0,
                                                        max_value=31.25, min_value=0, step=0.25, on_enter=True,
                                                        callback=self._update_frx_attn, min_clamped=True,
                                                        max_clamped=True, format='%.2f', width=150)
                            dpg.add_spacer()
                            t11 = dpg.add_text("Temperature (C)", color=(37, 37, 37))
                            self._temp_id = dpg.add_text("0.0", tag="frx_temp", color=(69,69,69))
                            dpg.add_spacer()
                            t12 = dpg.add_text("Serial Number", color=(37, 37, 37))
                            self._frx_sn_id = dpg.add_text("0x0000", tag="frx_sn", color=(69,69,69))
                            dpg.add_spacer()
            with dpg.child_window(tag="console_window", width=810, height=110) as win1:
                dpg.add_text("Welcome to the console.")
                dpg.add_text("Connect to the RF over Fiber boards to begin.")

        dpg.bind_font(default_font)
        dpg.bind_item_font(h1, second_font)
        dpg.bind_item_font(h2, second_font)

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

        dpg.bind_item_theme(ftx_win, global_theme)
        dpg.bind_item_theme(frx_win, global_theme)
        # dpg.bind_item_theme(main, global_theme)

        with dpg.theme() as console_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (37, 37, 37), category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)

        dpg.bind_item_theme(win1, console_theme)
        dpg.bind_item_font(win1, console_font)

        dpg.bind_item_font(t1, bold_font)
        dpg.bind_item_font(t2, bold_font)
        dpg.bind_item_font(t22, bold_font)
        dpg.bind_item_font(t3, bold_font)
        dpg.bind_item_font(t4, bold_font)
        dpg.bind_item_font(t5, bold_font)
        dpg.bind_item_font(t6, bold_font)
        dpg.bind_item_font(t7, bold_font)
        dpg.bind_item_font(t13, bold_font)
        dpg.bind_item_font(t14, bold_font)
        dpg.bind_item_font(t15, bold_font)

        dpg.bind_item_font(t8, bold_font)
        dpg.bind_item_font(t9, bold_font)
        dpg.bind_item_font(t10, bold_font)
        dpg.bind_item_font(t11, bold_font)
        dpg.bind_item_font(t12, bold_font)

        # dpg.show_style_editor()
