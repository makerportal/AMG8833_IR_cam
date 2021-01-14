#######################################################
# Registers for Reading/Writing to AMG8833 via I2C
# --- Based on AMG88xx Specification by Panasonic
#
# by Joshua Hrisko
#    Copyright 2021 | Maker Portal LLC
#
#######################################################
#
import smbus # i2c bus
#
#############################
# Device/I2C Info
#############################
#
GE_I2C_ADDRESS           = 0X69
RPI_BUS                  = 0X01
#
#############################
# Base Register Addresses
#############################
#
GE_POWER_CTL_REG         = 0x00 #///< Setting operating mode of device
GE_RESET_REG             = 0x01 #///< Writing to reset software. 
GE_FPSC_REG              = 0x02 #///< Setting Frame Rate
GE_INT_CTL_REG           = 0x03 #///< Setting Interrupt Function.
GE_STAT_REG              = 0x04 #///< Indicate Overflow Flag and Interrupt Flag
GE_SCLR_REG              = 0x05 #///< Status Clear Register
GE_AVE_REG               = 0x07 #///< Setting moving average Output Mode
GE_INTHL_REG             = 0x08 #///< Interrupt upper value - Upper level
GE_INTHH_REG             = 0x09 #///< Interrupt upper value - Upper level
GE_INTLL_REG             = 0x0A #///< Interrupt lower value - Lower level
GE_INTLH_REG             = 0x0B #///< Interrupt lower value - upper level
GE_IHYSL_REG             = 0x0C #///< Interrupt hysteresis value - Lower level
GE_IHYSH_REG             = 0x0D #///< Interrupt hysteresis value - Lower level
GE_TTHL_REG              = 0x0E #///< Thermistor Output Value - Lower level
GE_TTHH_REG              = 0x0F #///< Thermistor Output Value - Upper level
GE_INT0_REG              = 0x10 #///< Pixel 1->8 Interrupt Result 
GE_INT1_REG              = 0x11 #///< Pixel 9->16 Interrupt Result  
GE_INT2_REG              = 0x12 #///< Pixel 17->24 Interrupt Result 
GE_INT3_REG              = 0x13 #///< Pixel 25->32 Interrupt Result 
GE_INT4_REG              = 0x14 #///< Pixel 33->40 Interrupt Result
GE_INT5_REG              = 0x15 #///< Pixel 41->48 Interrupt Result  
GE_INT6_REG              = 0x16 #///< Pixel 49->56 Interrupt Result
GE_INT7_REG              = 0x17 #///< Pixel 57->64 Interrupt Result

GE_PIXEL_BASE            = 0x80 #///< Pixel 1 Output Value (Lower Level)
#
#############################
# Base Write Registers
#############################
#
# GE_POWER_CTL_REG - Operating Modes
GE_PCTL_NORMAL_MODE            = 0x00 
GE_PCTL_SLEEEP_MODE            = 0x10 
GE_PCTL_STAND_BY_60S_MODE      = 0x20
GE_PCTL_STAND_BY_10S_MODE      = 0x21
# GE_RESET_REG - Software Resets
GE_RST_FLAG_RST                = 0x30
GE_RST_INITIAL_RST             = 0x3F
# GE_FPSC_REG - Sample Rate Settings
GE_FPSC_1FPS                   = 0x01
GE_FPSC_10FPS                  = 0x00
# GE_INT_CTL_REG - Interrupt Settings
GE_INTC_ABS                    = 0b00000001
GE_INTC_DIF                    = 0b00000011
GE_INTC_OFF                    = 0b00000000
# GE_STAT_REG - Overflow/Interrupt Settings
GE_SCLR_CLR                   = 0b00000110
#
##################################
# I2C Bus Initializaiton and
# Register Read/Write Commands
##################################
#
def get_i2c_device(address, busnum, i2c_interface=None, **kwargs):
    return i2c_driver(address, busnum, i2c_interface, **kwargs)

class i2c_driver(object):
    def __init__(self, address, busnum, i2c_interface=None):
        self._address = address
        # specify smbus for RPi (smbus 1 for RPi 2,3,4)
        self._bus = smbus.SMBus(busnum)

    def write8(self, register, value):
        # write 8-bits to specified register
        value = value & 0xFF
        self._bus.write_byte_data(self._address, register, value)

    def read16(self, register, little_endian=True):
        # read 16-bits from specified register
        result = self._bus.read_word_data(self._address,register) & 0xFFFF
        if not little_endian:
            result = ((result << 8) & 0xFF00) + (result >> 8)
        return result
    
class AMG8833(object):
    def __init__(self,addr=GE_I2C_ADDRESS,bus_num=RPI_BUS):
        self.device=get_i2c_device(addr,bus_num)

        self.set_sensor_mode(GE_PCTL_NORMAL_MODE) # set sensor mode
        self.reset_flags(GE_RST_INITIAL_RST) # reset at startup
        self.set_interrupt_mode(GE_INTC_OFF) # set interrupt mode
        self.set_sample_rate(GE_FPSC_10FPS) # set sample rate

    def set_sensor_mode(self,mode):
        self.device.write8(GE_POWER_CTL_REG,mode) # mode
        
    def reset_flags(self,value):
        self.device.write8(GE_RESET_REG,value) # reset
        
    def set_sample_rate(self,value):
        self.device.write8(GE_FPSC_REG,value) # sample rate
        
    def set_interrupt_mode(self,mode):
        self.device.write8(GE_INT_CTL_REG,mode) # interrupts
        
    def clear_status(self,value):
        self.device.write8(GE_SCLR_REG,value) # overflows
        
    def read_temp(self,PIXEL_NUM):
        T_arr = [] # temp array
        status = False # status boolean for errors
        for i in range(0, PIXEL_NUM):
            raw = self.device.read16(GE_PIXEL_BASE + (i << 1))		
            converted = self.twos_compl(raw) * 0.25
            if converted<-20 or converted>100:
                return True,T_arr # return error if outside temp window
            T_arr.append(converted)
        return status,T_arr
    
    def read_thermistor(self):
        raw = self.device.read16(GE_TTHL_REG) # read thermistor (background temp)
        return self.signed_conv(raw)*0.0625 # scaling values 0.0625
    
    def twos_compl(self, val): # conversion for pixels
        if  0x7FF & val == val:
            return float(val)
        else:
            return float(val-4096)
        
    def signed_conv(self,val): # conversion for thermistor
        if 0x7FF & val == val:
            return float(val)
        else:
            return -float(0x7FF & val)
        
