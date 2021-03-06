from subprocess import Popen, PIPE,STDOUT
import time,os,signal
from utils import logger
import logging
from threading  import Thread,Event
from queue import Queue, Empty

class ZFitsWriter:
    '''
    Wrapper around the ZFitsWriter

    |------------------------------------------------------------------------------|
    |---------------------------------ZFITS WRITER---------------------------------|
    |-----------------------A compressed FITS writer module------------------------|
    |-It subscribes to streams, sorts out incoming events and writes them to disk--|
    |------------------------------------------------------------------------------|
    Required parameters:
    --output_dir the directory where to write the FITS files
    --input      the zmq input streams config(s)

    Optional arguments, in bytes if applicable:
    --id                the identifier to associate to this writer (for load
                        balancing)
    --max_evts_per_file the number of events to write to a given file before opening
                        a new one. default=100k
     --evts_per_tile     number of events to group and compress at once. default=100
     --num_comp_threads  number of threads to use for compressing data. default=0
     --max_comp_mem      maximum amount of memory to use for compression. default=2GB
     --max_file_size     maximum size of each uncompressed file in MegaBytes. Due to
                         compression, actual files will probably be smaller. default=
                         2GB
     --comp_scheme       which compression scheme to use. default=zrice.
                         available=raw, zlib, fact, diffman16, huffman16,
                         doublediffman16, riceman16, factrice, ricefact, rrice, rice,
                         lzo, zrice, zrice32, lzorice.
    --comp_block_size   size of the the blocks to use for compression. Increase if
                           exception is raised because of blocks too small.
                        default=2880kB
    --head_flush_inter  duration in milliseconds between two flush of the output
                        files header. Default is 10 seconds, 0 disables flushing
    --loop              loops (infinitely) after a run has stopped and continue
                        writing.
    --suffix            add a given suffix in the filename, e.g. a run type

    '''

    def __init__(self,log_location):
        self.writer = None
        self.output_dir = None
        self.input = 'tcp://localhost:13581'
        self.loop = True
        self.max_evts_per_file = 10000
        self.num_comp_threads = 5
        self.comp_scheme = 'zrice'
        self.max_comp_mem = 5000
        self.max_file_size = 5000
        self.suffix = ''
        self.run_number_in_suffix = True
        logger.initialise_logger(logname='ZFitsWriter',
                                            logfile='%s/%s.log' % (log_location,'zfitswriter'),stream=False)
        self.log = logging.getLogger('ZFitsWriter')
        self.log_thread = None
        self.log_queue = None
        self.stop_event = None

    def configuration(self, config):
        """
        Config is a dictionnary whose key correspond to the private members of the ZFitsWriter
        :param config:
        :return:
        """
        for key , val in config.items():
            if hasattr(self,key):
                setattr(self,key,val)

    def update_run_number(self,n):
        if self.run_number_in_suffix:
            self.suffix = 'run_%d'%n


    def log_subprocess_output(self,pipe):
        for line in iter(pipe.readline, b''):  # b'\n'-separated lines
            self.log.info('%r', line)

    def enqueue_output(self,q,out,stop_event):
        while not stop_event.is_set():
            for line in iter(out.readline, b''):
                self.log.info('%r', line)

    def start_writing(self):
        list_param = []
        for k,v in self.__dict__.items():
            if type(v).__name__ in ['function','Logger','dict','None']: continue
            if k in ['writer','log','current','_final','log_thread','logger_dir','log_thread','log_queue','stop_event','run_number_in_suffix']: continue
            if k == 'loop' and v :
                list_param +=['--%s'%k]
            else :
                list_param +=['--%s'%k,str(getattr(self,k))]
        list_param = ['/data/software/DAQ/CamerasToACTL/Build.Release/bin/ZFitsWriter']+list_param
        str_param = ''
        for p in list_param:
            str_param = str_param+ p + ' '
        self.log.info('Running %s'%str_param)

        self.writer = Popen(str_param,
                            stdout = PIPE,
                            stderr =STDOUT,shell=True, preexec_fn=os.setsid)
                            #env=dict(os.environ, my_env_prop='value'))


        if not self.log_queue : self.log_queue = Queue()
        if not self.stop_event: self.stop_event= Event()
        self.log_thread = Thread(target=self.enqueue_output, args=(self.log_queue ,self.writer.stdout,self.stop_event))
        self.log_thread.daemon = True  # thread dies with the program
        self.stop_event.clear()
        self.log_thread.start()

        return

    def stop_writing(self):
        os.killpg(os.getpgid(self.writer.pid), signal.SIGTERM)
        self.writer.wait()
        self.stop_event.set()
        self.log_thread.join()