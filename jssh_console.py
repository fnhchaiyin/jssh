# -*- coding: utf-8 -*-
import re
import readline
from threading import Thread,Semaphore
from datetime import datetime
import gl
from server import *
import platform
from cPickle import dump,load
from progressbar import *
reload(sys)
sys.setdefaultencoding('utf8')
COMMANDS = ['help','open_list','show','connect', 'exec_cmd', 'getfile',
            'sendfile', 'disconnect','threads_num','quit']
show_cmd=['hosts_status','history_cmd','thread_num','result','err']
class Completer(object):

    def _listdir(self, root):
        "List directory 'root' appending the path separator to subdirs."
        res = []
        for name in os.listdir(root):
            path = os.path.join(root, name)
            if os.path.isdir(path):
                name += os.sep
            res.append(name)
        return res

    def _complete_path(self, path=None):
        "Perform completion of filesystem path."
        if not path:
            return self._listdir('.')
        dirname, rest = os.path.split(path)
        if dirname:
            tmp = dirname
        else:
            tmp = '.'
        res = [os.path.join(dirname, p) for p in self._listdir(tmp) if p.startswith(rest)]
        # more than one match, or single match which does not exist (typo)
        if len(res) > 1 or not os.path.exists(path):
            return res
        # resolved to a single directory, so return list of files below it
        if os.path.isdir(path):
            return [os.path.join(path, p) for p in self._listdir(path)]
        # exact file match terminates this completion
        return [path + ' ']
    def complete_open_list(self, args):
        if not args:
            return self._complete_path('.')
        # treat the last arg as a path and complete it
        return self._complete_path(args[-1])
    def complete_getfile(self, args):
        if not args:
            return self._complete_path('.')
        # treat the last arg as a path and complete it
        return self._complete_path(args[-1])
    def complete_sendfile(self, args):
        if not args:
            return self._complete_path('.')
        # treat the last arg as a path and complete it
        return self._complete_path(args[-1])
    def complete_show(self, args):
        if not args:
            return [c for c in show_cmd]
        else:
            return [c+' ' for c in show_cmd if c.startswith(args[-1])]
    def complete(self, text, state):
        "Generic readline completion entry point."
        buffer = readline.get_line_buffer()
        line = readline.get_line_buffer().split()
        # show all commands
        if not line:
            return [c + ' ' for c in COMMANDS][state]
        # account for last argument ending in a space
        RE_SPACE = re.compile('.*\s+$', re.M)
        if RE_SPACE.match(buffer):
            line.append('')
        # resolve command to the implementation function
        cmd = line[0].strip()
        if cmd in COMMANDS:
            impl = getattr(self, 'complete_%s' % cmd)
            args = line[1:]
            if args:
                return (impl(args) + [None])[state]
            return [cmd + ' '][state]
        results = [c + ' ' for c in COMMANDS if c.startswith(cmd)] + [None]
        return results[state]
if platform.system()=='Linux':
    jssh_home=os.environ['HOME']+"/jssh"
    try:
        os.makedirs(jssh_home)
    except:
        pass
    gl.logfile=jssh_home+'/log.txt'
    gl.history_file=jssh_home+'/history.data'
elif platform.system()=='Windows':
    try:
        os.makedirs(r'c:\jssh')
    except:
        pass
    gl.logfile=r'c:\jssh\log.txt'
    gl.history_file=r'c:\jssh\history.data'
else:
    sys.stdout.write('system type is not supported')
if os.path.isfile(gl.history_file):
    pass
else:
    open(gl.history_file,'w').write('''(lp1
S'df -h'
p2
aS'ifconfig'
a.
''')
comp = Completer()
# we want to treat '/' as part of a word, so override the delimiters
readline.set_completer_delims(' \t\n;')
readline.parse_and_bind("tab: complete")
readline.set_completer(comp.complete)
def help():
    sys.stdout.write('''
    DESCRIPTION:
        A ssh tool,Excut command,Down load file from hosts,Send file to hosts
        open_list:
            Open a list file of hosts,like:192.168.2.3 22 root password
        connect:
            Connect to all the hosts
        exec_cmd:
            Excut a command,like:exec_cmd df -h
        get_file:
            Get a file from hosts
        send_file:
            Send a file to hosts
        disconnect:
            Disconnect from all the hosts
        show:
            Display state
            show err:Display the last error message
            show result:Display the last result
            show history_cmd:Display history command
            show hosts_status:show hosts status
        threads_num:
            Set number of threads,default 10

    \n''')
def open_list(list=''):
    #open list file
    try:
        list = ri.split()[1]
    except Exception,e:
        sys.stdout.write(str(e)+'\n')
    if list:
        save_log(log='%s open list %s\n' % (datetime.now(), list))
        try:
            server_list = open(list)
        except:
            server_list=None
            sys.stdout.write("open file failed !\n")
        if server_list:
            gl.server_all.clear()
            for (num, value) in enumerate(server_list):
                if len(value) > 4 and not value.startswith('#'):
                    try:
                        ip_addr = value.split()[0]
                    except:
                        pass
                    try:
                        if gl.server_all[ip_addr]:
                            err='ERROR,At line %s:Duplicate ipaddr %s' % (num,ip_addr)
                            print(err)
                            save_log(log=err)
                    except:
                        pass
                    try:
                        try:
                            port = int(value.split()[1])
                        except:
                            port = 22
                        username = value.split()[2]
                        password = value.split()[3]
                        gl.server_all[ip_addr] = server(ip=ip_addr, port=port, username=username, password=password)
                    except IndexError:
                        err = '\033[41;37mERROR,At line %s,wrong host info: %s\033[0m' % (num + 1, ip_addr)
                        print(err)
                        save_log(log=err)
            server_list.close()
            cmd_log.flush()
    else:
        print("Miss service list file name!")
def connect():
    if gl.server_all:
        semaphore= Semaphore(gl.thread_num)
        def connect_do(i):
            if semaphore.acquire():
                gl.server_all[i].connect()
            semaphore.release()
        print('Connecting,Please wait ...')
        threads = []
        for i in gl.server_all.keys():
            if not gl.server_all[i].connect_status:
                i = Thread(target=connect_do,args=(i,),name=i)
                i.start()
                threads.append(i)
        bar = ProgressBar(total=len(threads))
        bar.show()
        while True:
            for a in threads:
                if not a.isAlive():
                    bar.move()
                    bar.show()
                    threads.remove(a)
            if not threads:
                print('Connect completed')
                break
        gl.connected=False
        for i in gl.server_all.keys():
            if gl.server_all[i].connect_status:
                gl.connected=True
    else:
        print("Please open a service list file frist!")
def disconnect():
    semaphore= Semaphore(gl.thread_num)
    def disconnect_do(i):
        if semaphore.acquire():
            gl.server_all[i].close()
        semaphore.release()
    if gl.connected:
        threads = []
        for i in gl.server_all.keys():
            if gl.server_all[i].connect_status:
                i = Thread(target=disconnect_do,args=(i,),name=i)
                i.start()
                threads.append(i)
        for a in threads:
            a.join()
def exec_cmd():
    if gl.connected:
        semaphore= Semaphore(gl.thread_num)
        def gexe_do(i,cmd):
            if semaphore.acquire():
                gl.server_all[i].exec_cmd(cmd)
            semaphore.release()
        gcmd = re.split('\s+',ri,1)[1]
        if gcmd:
            sys.stdout.write('%s    exec cmd: %s;thread num:%s\n' % (datetime.now(), gcmd,gl.thread_num))
            save_log(log='%s    exec cmd: %s;thread num:%s\n' % (datetime.now(), gcmd,gl.thread_num))
            gl.history_cmd.reverse()
            del gl.history_cmd[1000:]
            gl.history_cmd.append(gcmd)
            gl.history_cmd.reverse()
            history_file = open(gl.history_file, 'w')
            dump(gl.history_cmd, history_file)
            history_file.close()
            threads = []
            for i in gl.server_all.keys():
                gl.server_all[i].err=''
                gl.server_all[i].result=''
                a = Thread(target=gexe_do,kwargs={'i':i,'cmd':gcmd},name=i)
                a.start()
                threads.append(a)
            bar = ProgressBar(total=len(threads))
            host_count=len(threads)
            bar.show()
            while True:
                    for a in threads:
                        if not a.isAlive():
                            bar.move()
                            bar.show()
                            if gl.server_all[a.getName()].err:
                                # sys.stdout.write( "\033[41;37m--------------------------------------%s\033[0m\n" % a.getName())
                                # sys.stdout.write("\033[41;37m%s\033[0m\n" % gl.server_all[a.getName()].err)
                                # sys.stdout.write(gl.server_all[a.getName()].result+'\n')
                                save_log(log="--------------------------------------%s\n" % a.getName())
                                save_log(log=gl.server_all[a.getName()].err+'\n')
                                save_log(log=gl.server_all[a.getName()].result+'\n')
                            elif gl.server_all[a.getName()].result:
                                # sys.stdout.write( "--------------------------------------%s\n" % a.getName())
                                # sys.stdout.write(gl.server_all[a.getName()].result+'\n')
                                save_log(log="--------------------------------------%s\n" % a.getName())
                                save_log(log=gl.server_all[a.getName()].result+'\n')
                            threads.remove(a)
                    if not threads:
                        break
            err_count=0
            resoult_count=0
            for i in gl.server_all.keys():
                if gl.server_all[i].err:
                    err_count+=1
                if gl.server_all[i].result:
                    resoult_count+=1
            print("######################all the servers finished execcmd:%s (%s)" % (gcmd,datetime.now()))
            print("host:%s\nerr:%s\nresoult:%s" %(host_count,err_count,resoult_count))
            save_log(log="######################all the servers finished execcmd:%s (%s)\n" % (gcmd,datetime.now()))
            cmd_log.flush()
        else:
            sys.stdout.write("Entry a command to exec!\n")
    else:
        sys.stdout.write("Please Connect frist!\n")
def getfile():
    pass
def sendfile():
    pass
def threads_num():
    try:
        gl.thread_num=int(re.split('\s+',ri,1)[1])
    except:
        gl.thread_num=10

cmd_log = open(gl.logfile, 'a')
gl.thread_num=10
def save_log(log=''):
    cmd_log.write(log)
def show():
    def err():
        for i in gl.server_all.keys():
            if gl.server_all[i].err:
                print( "--------------------------------------%s" % i)
                print gl.server_all[i].err
        print 'END'
    def result():
        for i in gl.server_all.keys():
            if gl.server_all[i].result:
                print( "--------------------------------------%s" % i)
                print gl.server_all[i].result
        print 'END'
    def thread_num():
        sys.stdout.write("thread_num =%s\n" % gl.thread_num)
    def history_cmd():
        history_file = open(gl.history_file, 'r')
        try:
            gl.history_cmd = (load(history_file))
        except:
            os.rename(gl.history_file,'%s_%s' % (gl.history_file,strftime("%Y-%m-%d_%H_%M")))
            open(gl.history_file,'w').write('''(lp1
S'df -h'
p2
aS'ifconfig'
a.
''')
        history_file.close()
        for i in gl.history_cmd:
            print i
        print 'END'
    def hosts_status():
        for i in gl.server_all.keys():
            if not gl.server_all[i].connect_status:
                print '%s\t\t\033[41;37mnot connected\033[0m' % i
            else:
                print i,'connected'
        print 'END'
    try:
        option=ri.split()[1]
    except:
        option=''
    if option in show_cmd:
        eval(option)()
    else:
        print "\033[41;37mWrong option!\033[0m"
while True:
    try:
        ri=raw_input('\033[;32m[jssh]#\033[0m')
        if ri:
            cmdstr=ri.split()[0]
            if cmdstr in COMMANDS:
                if cmdstr=='quit':
                    break
                else:
                    # Thread(target=eval(cmdstr)).start()
                    eval(cmdstr)()
            else:
                print('\033[41;37m Unnkown command! \033[0m')
    except  (IOError,EOFError,KeyboardInterrupt),e:
        print str(e)
    