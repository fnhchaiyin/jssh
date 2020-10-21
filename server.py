# -*- coding: utf-8 -*-  
#报错信息为弹出框
from paramiko import *
util.log_to_file("paramiko.log")
import socket
import os
class server(object):
    '''
    ip,port,username,password
    '''
    def __init__(self,ip = '',port = '',username = '',password = ''):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.send_file_status = 'false'
        self.get_file_status = 'false'
        self.result = ''
        self.err = ''
        self.connect_status=False
        self.selected=''
    def connect(self):
        try:
            self.ssh = SSHClient()
            self.ssh.load_system_host_keys()
            self.ssh.set_missing_host_key_policy(AutoAddPolicy())
            self.ssh.connect(self.ip,self.port,self.username,self.password,timeout=30)
            self.connect_status=True
        except AuthenticationException:
            self.err = 'Authentication failed,please check your username and password!\n'
        except socket.timeout:
            self.err = 'Timeout\n'
        except Exception,e:
            self.err = str(e)

    def exec_cmd(self,cmd=''):
        if self.connect_status:
            try:
                stdin,stdout,stderr= self.ssh.exec_command(cmd)
                self.result = self.result + ''.join(stdout.readlines())
                self.err = self.err + ''.join(stderr.readlines())
            except AttributeError:
                err = 'Error:Connection failed,command \'%s\' execued failed\n' %(cmd)
                self.err = self.err + err
            except UnicodeDecodeError:
                err = 'The command \'%s\' execed successful,but can not display the result,use:\'echo $LANG\' to check\n' %(cmd)
                self.err += err
            except Exception,e:
                self.err += str(e)
        else:
            err = 'Not connected!\n'
            self.err = self.err + err
    def FileTransfer(self,lo_path='',lo_file='',re_path='',re_file='',FileSend = 0):
        try:
            tcpsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            tcpsock.settimeout(5)
            tcpsock.connect((self.ip,self.port),)
            ssh = Transport(tcpsock)
            ssh.connect(username=self.username,password=self.password)
            sftpConnect=SFTPClient.from_transport(ssh)
            if FileSend == 0:
                file3 = '%s_%s' %(os.path.basename(re_file),self.ip)
                sftpConnect.get(re_file,os.path.join(lo_path,file3))
                self.get_file_status = 'successful'
            else:
                sftpConnect.put(lo_file,re_file)
                self.send_file_status = 'successful'
        except socket.timeout:
            self.err='Error:connect time out!'
        except Exception,e:
            self.err=str(e)
    def close(self):
        self.ssh.close()
        self.connect_status=False
    def clear(self):
        self.send_file_status = 'false'
        self.get_file_status = 'false'
        self.result = ''
        self.err = ''
    def __del__(self):
        try:
            self.ssh.close()
        except:
            pass
