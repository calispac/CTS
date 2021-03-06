import pickle
import logging,sys
import numpy as np
from cts_core.cameratestsetup import CTS
ac_led_calib = pickle.load( open('/data/software/CTS/config/ac_led_calib_spline_120.p' , "rb" ) )
ac_patch_calib = pickle.load( open('/data/software/CTS/config/ac_patch_calib_spline_120.p' , "rb" ) )


f = open('/data/software/CTS/config/dc_led_calib_spline_120.txt')
coeffs = np.zeros((528,2),dtype = float)
lines = f.readlines()
dc_led_calib = {}
cts = CTS('/data/software/CTS/config/cts_config_120.cfg','/data/software/CTS/config/camera_config.cfg',angle=120.)
cts_old = CTS('/data/software/CTS/config/cts_config_120_old.cfg','/data/software/CTS/config/camera_config.cfg',angle=120.)
pixel_list = list(cts.pixel_to_led['DC'].keys())
pixel_list_old = list(cts_old.pixel_to_led['DC'].keys())
pixel_list.sort()
dc_led_calib_byled = {}
for i,l in enumerate(lines):
    dc_led_calib[pixel_list[i]]={}
    val=l.split('\n')[0].split(' ')
    for j in range(2):
        coeffs[i,j]=val[j]
    for j in range(1000):
        nsb = coeffs[i, 0] * np.exp(coeffs[i, 1] * j)
        if nsb > 10.e6:
            dc_led_calib[pixel_list[i]]['DAC']=j
            dc_led_calib[pixel_list[i]]['NSB']=nsb
            dc_led_calib[pixel_list[i]]['LED']=cts.pixel_to_led['DC'][pixel_list[i]]
            dc_led_calib_byled[cts.pixel_to_led['DC'][pixel_list[i]]]={
                'DAC':j,
                'NSB':nsb
            }
dc_board_calib = {}
dc_board_calib_byled = {}
for j in range(1000):
    for board in cts.LED_boards:
        nsbs,nsb,counter = 0.,0.,0
        for l,led in enumerate(board.LEDs):
            if led.internal_id not in dc_led_calib_byled.keys() : continue
            nsbs+=dc_led_calib_byled[led.internal_id]['NSB']
            counter+=1
        if counter>0.:
            nsb = nsbs/counter
        dc_board_calib[cts.camera.Pixels[board.leds_camera_pixel_id[0]].fadc_unique] = {
            'LED':board.internal_id,
            'NSB': nsb,
            'DAC':j
        }
        dc_board_calib_byled[board.internal_id] = {
            'LED':board.internal_id,
            'NSB': nsb,
            'DAC':j
        }

f.close()



# revert by LED and LED Patch
ac_led_calib_byled = {}
for k in ac_led_calib.keys():
    ac_led_calib_byled[ac_led_calib[k]['LED']]={
        'DAC':ac_led_calib[k]['DAC'],
        'NPE':ac_led_calib[k]['NPE']
    }
ac_patch_calib_byled = {}
for k in ac_patch_calib.keys():
    ac_patch_calib_byled[ac_patch_calib[k]['LED']]={
        'DAC':ac_patch_calib[k]['DAC'],
        'NPE':ac_patch_calib[k]['NPE']
    }

## AC

def get_ACLED_DAC(npe,pixel):
    '''
    Return the DAC needed to reach npe in this pixel

    :param npe:
    :param pixel:
    :return:
    '''
    log = logging.getLogger(sys.modules['__main__'].__name__)
    if pixel in ac_led_calib.keys():
        return int(round(ac_led_calib[pixel]['DAC'][np.argmin(np.abs(ac_led_calib[pixel]['NPE']-npe))]))
    else :
        new_pix = np.argmin(np.abs(np.array(list(ac_led_calib.keys()))-pixel))
        log.debug('replace the calib of pixel',pixel,'by pixel',new_pix)
        return int(round(ac_led_calib[new_pix]['DAC'][np.argmin(np.abs(ac_led_calib[new_pix]['NPE']-npe))]))


def get_ACPATCH_DAC(npe,patch):
    '''
    Return the DAC needed to reach npe in this pixel patch

    :param npe:
    :param patch:
    :return:
    '''
    log = logging.getLogger(sys.modules['__main__'].__name__)
    if patch in ac_patch_calib.keys() and not (patch in [265,277,288,300]):
        return int(round(ac_patch_calib[patch]['DAC'][np.argmin(np.abs(ac_patch_calib[patch]['NPE']-npe))]))
    else :
        new_patch_key = np.argmin(np.abs(np.array(list(ac_patch_calib.keys()))-patch))
        new_patch = list(ac_patch_calib.keys())[new_patch_key]
        if patch in [265,277,288,300]:
            new_patch = 132
        log.debug('replace the calib of patch %d by patch %d'%(patch,new_patch))
        return int(round(ac_patch_calib[new_patch]['DAC'][np.argmin(np.abs(ac_patch_calib[new_patch]['NPE']-npe))]))

def get_ACLED_DAC_byled(npe,led):
    '''
    Return the DAC needed to reach npe in this led

    :param npe:
    :param led:
    :return:
    '''
    log = logging.getLogger(sys.modules['__main__'].__name__)
    if led in ac_led_calib_byled.keys():
        return int(round(ac_led_calib_byled[led]['DAC'][np.argmin(np.abs(ac_led_calib_byled[led]['NPE']-npe))]))
    else :
        new_led = np.argmin(np.abs(np.array(list(ac_led_calib_byled.keys()))-led))
        log.debug('replace the calib of led',led,'by led',new_led)
        return int(round(ac_led_calib_byled[new_led]['DAC'][np.argmin(np.abs(ac_led_calib_byled[new_led]['NPE']-npe))]))


def get_ACPATCH_DAC_byled(npe,patch):
    '''
    Return the DAC needed to reach npe in this led patch
    :param npe:
    :param patch:
    :return:
    '''
    log = logging.getLogger(sys.modules['__main__'].__name__)
    if patch in ac_patch_calib_byled.keys():
        return int(round(ac_patch_calib_byled[patch]['DAC'][np.argmin(np.abs(ac_patch_calib_byled[patch]['NPE']-npe))]))
    else :
        new_patch_key = np.argmin(np.abs(np.array(list(ac_patch_calib_byled.keys()))-patch))
        new_patch = list(ac_patch_calib_byled.keys())[new_patch_key]
        log.debug('replace the calib of patch %d by patch %d'%(patch,new_patch))
        return int(round(ac_patch_calib_byled[new_patch]['DAC'][np.argmin(np.abs(ac_patch_calib_byled[new_patch]['NPE']-npe))]))


## DC

def get_DCLED_DAC(nsb, pixel):
    '''
    Return the DAC needed to reach nsb in this pixel

    :param nsb:
    :param pixel:
    :return:
    '''
    log = logging.getLogger(sys.modules['__main__'].__name__)
    if pixel in dc_led_calib.keys():
        return int(round(dc_led_calib[pixel]['DAC'][np.argmin(np.abs(dc_led_calib[pixel]['NSB'] - nsb))]))
    else:
        new_pix = np.argmin(np.abs(np.array(list(dc_led_calib.keys())) - pixel))
        log.debug('replace the calib of pixel', pixel, 'by pixel', new_pix)
        return int(round(dc_led_calib[new_pix]['DAC'][np.argmin(np.abs(ac_led_calib[new_pix]['nsb'] - nsb))]))


def get_DCBOARD_DAC(nsb, fadc_unique):
    '''
    Return the DAC needed to reach nsb in this pixel patch

    :param nsb:
    :param patch:
    :return:
    '''
    nsb = float(nsb)
    log = logging.getLogger(sys.modules['__main__'].__name__)
    if fadc_unique in dc_board_calib.keys():
        print(dc_board_calib[fadc_unique])

        return int(round(dc_board_calib[fadc_unique]['DAC'][np.argmin(np.abs(dc_board_calib[fadc_unique]['NSB'] - nsb))]))
    else:
        5./0
        return 'problem'


def get_DCLED_DAC_byled(nsb, led):
    '''
    Return the DAC needed to reach nsb in this led

    :param nsb:
    :param led:
    :return:
    '''
    log = logging.getLogger(sys.modules['__main__'].__name__)
    if led in dc_led_calib_byled.keys():
        return int(round(dc_led_calib_byled[led]['DAC'][np.argmin(np.abs(dc_led_calib_byled[led]['NSB'] - nsb))]))
    else:
        new_led = np.argmin(np.abs(np.array(list(dc_led_calib_byled.keys())) - led))
        log.debug('replace the calib of led', led, 'by led', new_led)
        return int(round(dc_led_calib_byled[new_led]['DAC'][np.argmin(np.abs(dc_led_calib_byled[new_led]['NSB'] - nsb))]))


def get_DCBOARD_DAC_byled(nsb, patch):
    '''
    Return the DAC needed to reach nsb in this led patch
    :param nsb:
    :param patch:
    :return:
    '''
    log = logging.getLogger(sys.modules['__main__'].__name__)
    if patch in dc_board_calib_byled.keys():
        return int(round(dc_board_calib_byled[patch]['DAC'][np.argmin(np.abs(dc_board_calib_byled[patch]['NSB'] - nsb))]))
    else:
        new_patch = np.argmin(np.abs(np.array(list(dc_board_calib_byled.keys())) - patch))
        log.debug('replace the calib of patch', patch, 'by patch', new_patch)
        return int(round(dc_board_calib_byled[new_patch]['DAC'][np.argmin(np.abs(dc_board_calib_byled[new_patch]['NSB'] - nsb))]))
