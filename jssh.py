# -*- coding: utf-8 -*-  
# 报错信息为弹出框
#修改多线程
#执行进度优化
from Tkinter import *
from tkFileDialog import *
from threading import Thread,Semaphore
from datetime import datetime
import gl
from server import *
from ttk import Combobox
from tkFont import Font,NORMAL
# import atexit
from signal import signal,SIGTERM,SIGINT
import sys
import os
from cPickle import dump,load
from time import *
import platform
import re
# import tkMessageBox
def main():
    reload(sys)
    sys.setdefaultencoding('utf8')
    def find_it(event, i):
        target = "--------------------------------------%s\n" % i
        where = text.search(target, '0.0', END)
        if where:                                   
            pastit = where + ('+%dc' % len(target))  
            text.tag_add(SEL, where, pastit)   
            text.mark_set(INSERT, pastit)        
            text.see(INSERT)                   
            text.focus()
    def xshell(event,i):
        if gl.server_all[i].connect_status:
            shell = gl.server_all[i].ssh.invoke_shell()
            def send_ctrl_c(event):
                shell.send('\x03')
            def single_exec_cmd(event, i):
                cmd = xshell_entry.get()
                if cmd:
                    shell.send(cmd+'\x0a')
                    xshell_entry.delete(0, END)
                else:
                    shell.send('\x0a')
            xshell_top=Toplevel()
            xshell_top.attributes("-topmost", 1)
            xshell_top.title("%s@%s"%(gl.server_all[i].username,i))
            def on_closing():
                shell.close()
                xshell_top.destroy()
            xshell_top.protocol("WM_DELETE_WINDOW", on_closing)
            xshell_text = Text(xshell_top, bg='black', fg='green')
            xshell_scroll = Scrollbar(xshell_top, command=xshell_text.yview)
            xshell_text.configure(yscrollcommand=xshell_scroll.set)
            xshell_scroll.pack(side=RIGHT, fill=Y)
            xshell_text.pack(fill=BOTH,expand=YES)
            xshell_Label=Label(xshell_top, text="command:")
            xshell_Label.pack(side=LEFT)
            xshell_entry = Entry(xshell_top, insertbackground='green', width=50)
            xshell_entry.bind('<Key-Return>',lambda event,i=i:single_exec_cmd(event,i))
            xshell_entry.bind('<Control-c>', send_ctrl_c)
            xshell_entry.pack(fill=X)
            def put_resoult():
                sleep(1)
                while True:
                    try:
                        xshell_text.insert(END,re.sub('\[.*?m','',shell.recv(1024)))
                        sleep(0.1)
                        xshell_text.see(END)
                    except:
                        break
            Thread(target=put_resoult).start()
        else:
            tl = Toplevel() 
            tl.attributes("-topmost", 1)
            tl.title("ERROR")
            err_text = Label(tl, bg='black', fg='red',width=50, height=10, text="The host is not be connected!\n")
            err_text.pack(fill=BOTH)
    def open_list():
        # 选择服务器清单
        fd = askopenfilename(initialdir='.') 
        if fd:
            save_log(log='%s open list %s\n' % (datetime.now(), fd))
            root.title('Current file list:%s' % fd)
            try:
                server_list = open(fd)
            except:
                text.insert(END, "open file failed !\n")
                server_list=None
            if server_list:
                gl.server_all.clear()
                if any(gl.cbuts):
                    for i in gl.cbuts.keys():
                        gl.cbuts[i].destroy()
                    gl.cbuts.clear()
                for (num, value) in enumerate(server_list):
                    if len(value) > 4 and not value.startswith('#'):
                        try:
                            hostname = value.split()[0]
                        except:
                            pass
                        try:
                            ipinfo = value.split()[1]
                            ip_addr = ipinfo.split(":")[0]
                        except:
                            pass
                        try:
                             if gl.server_all[hostname]:
                                 err='ERROR,At line %s:Duplicate hostname %s\n' % (num,hostname)
                                 text.insert(END, err)
                                 save_log(log=err)
                        except:
                             pass
                        try:
                             if gl.server_all[hostname].ip_addr+":"+gl.server_all[hostname].port:
                                 err='ERROR,At line %s:Duplicate ip and port %s\n' % (num,ipinfo)
                                 text.insert(END, err)
                                 save_log(log=err)
                        except:
                             pass
                        try:
                            try:
                                port = int(ipinfo.split(":")[1])
                            except:
                                port = 22
                            username = value.split()[2]
                            password = value.split()[3]
                            gl.server_all[hostname] = server(ip=ip_addr, port=port, username=username, password=password)
                            gl.server_all[hostname].selected = IntVar()
                            gl.cbuts[hostname] = (Checkbutton(listframe, text=hostname, font=ft, bg='black', foreground="blue", variable=gl.server_all[hostname].selected))
                            gl.cbuts[hostname].select()
                            gl.cbuts[hostname].pack()
                            gl.cbuts[hostname].bind("<Button-3>", lambda event, i=hostname:find_it(event, i))
                            gl.cbuts[hostname].bind("<Control-Button-1>", lambda event, i=hostname:xshell(event, i))
                        except IndexError:
                            err = 'ERROR,At line %s,wrong host info: %s\n' % (num + 1, value)
                            text.insert(END, err)
                            save_log(log=err)

                server_list.close()
                disconnect['state'] = DISABLED
            if any(gl.server_all):
                connect['state'] = ACTIVE
            cmd_log.flush()
    def connect():
        try:
            thread_num=int(thread_num_entry.get())
        except:
            thread_num=int(10)
        semaphore= Semaphore(thread_num)
        def connect_do(i):
            if semaphore.acquire():
                gl.server_all[i].connect()
            semaphore.release()
        connect['state'] = DISABLED
        text.insert(END,'Connecting,Please wait ...\n')
        threads = []
        for i in gl.server_all.keys():
            if gl.server_all[i].selected.get() == 1:
                if gl.server_all[i].connect_status:
                    pass
                else:
                    i = Thread(target=connect_do,args=(i,),name=i)
                    i.start()
                    threads.append(i)
                    sleep(0.02)
                    root.update()
        while True:
            for a in threads:
                sleep(0.02)
                root.update()
                if not a.isAlive():
                    sleep(0.02)
                    root.update()
                    if gl.server_all[a.getName()].err:
                        gl.cbuts[a.getName()]['foreground'] = "red"
                        try:
                            err_text.insert(END, "--------------------------------------%s\n" % a.getName())
                            err_text.insert(END, gl.server_all[a.getName()].err)
                            err_text.see(END)
                            gl.server_all[a.getName()].err = ''
                        except:
                            tl = Toplevel()
                            tl.attributes("-topmost", 1)
                            tl.title("ERROR")
        #                     def closetl():
        #                         err_topped=False
        #                     tl.protocol("WM_DELETE_WINDOW",closetl)
                            err_text = Text(tl, bg='black', fg='red')
                            err_scroll = Scrollbar(tl, command=err_text.yview)
                            err_text.configure(yscrollcommand=err_scroll.set)
                            err_scroll.pack(side=RIGHT, fill=Y)
                            err_text.pack(fill=BOTH,expand=YES)
                            err_text.insert(END, "--------------------------------------%s\n" % a.getName())
                            err_text.insert(END, gl.server_all[a.getName()].err)
                            err_text.see(END)
                            gl.server_all[a.getName()].err = ''
                        sleep(0.02)
                        root.update()
                        threads.remove(a)
                    if gl.server_all[a.getName()].connect_status:
                        gl.cbuts[a.getName()]['foreground'] = "green"
                        gl.connected = True
                        sleep(0.02)
                        root.update()
                        threads.remove(a)
            if not threads:
                text.insert(END,'Connect completed\n')
                #tkMessageBox.showinfo("Complete!", "Connect Complete!")
                break
        if gl.connected:
            disconnect['state'] = ACTIVE
            command_but['state'] = ACTIVE
            file_but['state'] = DISABLED
        connect['state'] = ACTIVE
    def disconnect():
        disconnect['state']=DISABLED
        try:
            thread_num=int(thread_num_entry.get())
        except:
            thread_num=int(10)
        semaphore= Semaphore(thread_num)
        def disconnect_do(i):
            if semaphore.acquire():
                gl.server_all[i].close()
            semaphore.release()
        if gl.connected:
            threads = []
            for i in gl.server_all.keys():
                if gl.server_all[i].selected.get() == 1:
                    gl.cbuts[i]['foreground'] = "blue"
                    i = Thread(target=disconnect_do,args=(i,),name=i)
                    i.start()
                    sleep(0.02)
                    root.update()
                    threads.append(i)
            for a in threads:
                a.join()
            gl.connected = False
            for r in gl.server_all.keys():
                if gl.server_all[r].connect_status:
                    gl.connected = True
        if gl.connected:
            disconnect['state'] = ACTIVE
            command_but['state'] = ACTIVE
            file_but['state'] = DISABLED
        else:
            disconnect['state'] = DISABLED
            connect['state'] = ACTIVE
            command_but['state'] = DISABLED
            file_but['state'] = ACTIVE
    def gexe_cmd():
        try:
            thread_num=int(thread_num_entry.get())
        except:
            thread_num=int(10)
        semaphore= Semaphore(thread_num)
        def gexe_do(i,cmd):
            if semaphore.acquire():
                gl.server_all[i].exec_cmd(cmd)
            semaphore.release()
        command_but['state'] = DISABLED
        gcmd = entry.get()
        save_log(log='%s    exec cmd: %s\n' % (datetime.now(), gcmd))
        gl.history_cmd.reverse()
        del gl.history_cmd[1000:]
        gl.history_cmd.append(gcmd)
        gl.history_cmd.reverse()
        entry['values'] = gl.history_cmd
        history_file = open(gl.history_file, 'w')
        dump(gl.history_cmd, history_file)
        history_file.close()
        threads = []
        wait_t = Toplevel()
        wait_t.attributes("-topmost", 1)
        wait_t.title("exec command:%s" % gcmd)
        w_text = Text(wait_t, bg='black', fg='green')
        w_scroll = Scrollbar(wait_t, command=w_text.yview)
        w_text.configure(yscrollcommand=w_scroll.set)
        w_scroll.pack(side=RIGHT, fill=Y)
        w_text.pack(fill=BOTH,expand=YES)
        sleep(0.02)
        clear()
        root.update()
        for i in gl.server_all.keys():
            if gl.server_all[i].selected.get() == 1:
                try:
                    w_text.insert(END,'%s\n' % i)
                except:
                    pass
                gl.cbuts[i]['foreground'] = "green"
                #a = Thread(target=gl.server_all[i].exec_cmd,kwargs={'cmd':"LANG=zh_CN.UTF-8;%s" % gcmd},name=i)
                a = Thread(target=gexe_do,kwargs={'i':i,'cmd':gcmd},name=i)
                a.start()
                sleep(0.02)
                root.update()
                threads.append(a)
        command_but['state'] = ACTIVE
        while True:
                for a in threads:
                    sleep(0.02)
                    root.update()
                    if not a.isAlive():
                        sleep(0.02)
                        root.update()
                        if gl.server_all[a.getName()].err:
                            gl.cbuts[a.getName()]['foreground'] = "red"
                            try:
                                where = w_text.search('%s\n' % a.getName(), '0.0', END)
                                if where:
                                    pastit = where + ('+%dc' % (len(a.getName())+1))
                                    w_text.delete(where, pastit)
                            except:
                                pass
                            try:
                                err_text.insert(END, "--------------------------------------%s\n" % a.getName())
                                save_log(log="--------------------------------------%s\n" % a.getName())
                                err_text.insert(END, gl.server_all[a.getName()].err)
                                save_log(log=gl.server_all[a.getName()].err)
                                err_text.see(END)
                                sleep(0.02)
                                root.update()
                            except:
                                tl = Toplevel()
                                tl.attributes("-topmost", 1)
                                tl.title("ERROR:execcmd %s" % gcmd)
                                err_text = Text(tl, bg='black', fg='red')
                                err_scroll = Scrollbar(tl, command=err_text.yview)
                                err_text.configure(yscrollcommand=err_scroll.set)
                                err_scroll.pack(side=RIGHT, fill=Y)
                                err_text.pack(fill=BOTH,expand=YES)
                                err_text.insert(END, "--------------------------------------%s\n" % a.getName())
                                save_log(log="--------------------------------------%s\n" % a.getName())
                                err_text.insert(END, gl.server_all[a.getName()].err)
                                save_log(log=gl.server_all[a.getName()].err)
                                err_text.see(END)
                                sleep(0.02)
                                root.update()
                        if gl.server_all[a.getName()].result:
                            try:
                                where = w_text.search('%s\n' % a.getName(), '0.0', END)
                                pastit = where + ('+%dc' % (len(a.getName())+1))
                                w_text.delete(where, pastit)
                            except:
                                pass
                            text.insert(END, "--------------------------------------%s\n" % a.getName())
                            save_log(log="--------------------------------------%s\n" % a.getName())
                            text.insert(END, gl.server_all[a.getName()].result)
                            text.see(END)
                            save_log(log=gl.server_all[a.getName()].result)
                            sleep(0.02)
                            root.update()
                        if not gl.server_all[a.getName()].result and not gl.server_all[a.getName()].err:
                            try:
                                where = w_text.search('%s\n' % a.getName(), '0.0', END)
                                if where:
                                    pastit = where + ('+%dc' % (len(a.getName())+1))
                                    w_text.delete(where, pastit)
                            except:
                                pass
                            sleep(0.02)
                        gl.server_all[a.getName()].err = ''
                        gl.server_all[a.getName()].result = ''
                        threads.remove(a)
                if not threads:
                    break
        text.insert(END, "######################all the servers finished execcmd:%s (%s)\n" % (gcmd,datetime.now()))
        save_log(log="######################all the servers finished execcmd:%s (%s)\n" % (gcmd,datetime.now()))
        try:
            if w_text.get(0.0,END).split():
                pass
            else:
                wait_t.destroy()
        except:
            pass
        cmd_log.flush()
        #tkMessageBox.showinfo("Complete!", "exec cmd :\n %s \n Complete!" % gcmd)
    def get_ui():
        global getfile_top
        getfile_top = Toplevel(root)
        getfile_top.attributes("-topmost", 1)
        getfile_top.title("get file")

        get_remote = Label(getfile_top, text="remote file:")
        get_remote.grid(row=0, column=0)
        global get_re
        get_re = Entry(getfile_top, insertbackground='green', width=50)
        get_re.grid(row=0, column=1)

        get_locate = Label(getfile_top, text="local dir:")
        get_locate.grid(row=1, column=0)
        global get_lo
        get_lo = Entry(getfile_top, insertbackground='green', width=50)
        get_lo.grid(row=1, column=1)
        def get_file_select():
            get_filename=askdirectory()
            get_lo.delete(0, END)
            get_lo.insert(END,get_filename)
        get_select_but=Button(getfile_top,text='...',command=get_file_select)
        get_select_but.grid(row=1,column=2)
        getfile_sub_but = Button(getfile_top, text='get', command=get_file)
        getfile_sub_but.grid(row=2)
    def get_file():
        try:
            thread_num=int(thread_num_entry.get())
        except:
            thread_num=int(10)
        semaphore= Semaphore(thread_num)
        def get_do(i,lo_path,re_file,FileSend):
            if semaphore.acquire():
                gl.server_all[i].FileTransfer(lo_path=lo_path,re_file=re_file,FileSend=FileSend)
            semaphore.release()
        re_file=get_re.get()
        lo_file=get_lo.get()
        if re_file and lo_file:
            try:
                gl.thread_num=int(thread_num_entry.get())
            except:
                gl.thread_num=int(10)
            save_log(log='%s    get file: %s\n' % (datetime.now(), re_file))
            threads = []
            wait_t = Toplevel()
            wait_t.attributes("-topmost", 1)
            wait_t.title("Get file:%s --> %s" % (re_file,lo_file))
            w_text = Text(wait_t, bg='black', fg='green')
            w_scroll = Scrollbar(wait_t, command=w_text.yview)
            w_text.configure(yscrollcommand=w_scroll.set)
            w_scroll.pack(side=RIGHT, fill=Y)
            w_text.pack(fill=BOTH,expand=YES)
            sleep(0.02)
            root.update()
            clear()
            getfile_top.destroy()
            for i in gl.server_all.keys():
                if gl.server_all[i].selected.get() == 1:
                    w_text.insert(END,'%s\n' % i)
                    a = Thread(target=get_do,kwargs={'i':i,'lo_path':lo_file,'re_file':re_file,'FileSend':0},name=i)
                    a.start()
                    threads.append(a)
                    sleep(0.02)
                    root.update()
            while True:
                for a in threads:
                    sleep(0.02)
                    root.update()
                    if not a.isAlive():
                        sleep(0.02)
                        root.update()
                        if gl.server_all[a.getName()].err:
                            gl.cbuts[a.getName()]['foreground'] = "red"
                            try:
                                where = w_text.search('%s\n' % a.getName(), '0.0', END)
                                if where:
                                    pastit = where + ('+%dc' % (len(a.getName())+1))
                                    w_text.delete(where, pastit)
                            except:
                                pass
                            try:
                                err_text.insert(END, "--------------------------------------%s\n" % a.getName())
                                save_log(log="--------------------------------------%s\n" % a.getName())
                                err_text.insert(END, gl.server_all[a.getName()].err)
                                save_log(log=gl.server_all[a.getName()].err)
                                err_text.see(END)
                                gl.server_all[a.getName()].err = ''
                                sleep(0.02)
                                root.update()
                            except:
                                tl = Toplevel()
                                tl.attributes("-topmost", 1)
                                tl.title("ERROR:get file %s --> %s (%s)\n" % (re_file,lo_file,datetime.now()))
                                err_text = Text(tl, bg='black', fg='red')
                                err_scroll = Scrollbar(tl, command=err_text.yview)
                                err_text.configure(yscrollcommand=err_scroll.set)
                                err_scroll.pack(side=RIGHT, fill=Y)
                                err_text.pack(fill=BOTH,expand=YES)
                                err_text.insert(END, "--------------------------------------%s\n" % a.getName())
                                save_log(log="--------------------------------------%s\n" % a.getName())
                                err_text.insert(END, gl.server_all[a.getName()].err)
                                save_log(log=gl.server_all[a.getName()].err)
                                err_text.see(END)
                                gl.server_all[a.getName()].err = ''
                                sleep(0.02)
                                root.update()
                            threads.remove(a)
                        elif gl.server_all[a.getName()].get_file_status:
                            try:
                                where = w_text.search('%s' % a.getName(), '0.0', END)
                                pastit = where + ('+%dc' % (len(a.getName())+1))
                                w_text.delete(where, pastit)
                            except:
                                pass
                            text.insert(END, "--------------------------------------%s\n" % a.getName())
                            save_log(log="--------------------------------------%s\n" % a.getName())
                            text.insert(END, "get file %s %s\n" % (re_file, gl.server_all[a.getName()].get_file_status))
                            save_log(log="get file %s %s\n" % (re_file, gl.server_all[a.getName()].get_file_status))
                            gl.server_all[a.getName()].result = ''
                            sleep(0.02)
                            root.update()
                            threads.remove(a)
                if not threads:
                    break

            text.insert(END, "######################all the servers finished get file:%s --> %s (%s)\n" % (re_file,lo_file,datetime.now()))
            save_log(log="######################all the servers finished get file:%s --> %s (%s)\n" % (re_file,lo_file,datetime.now()))
            if w_text.get(0.0, END).split():
                pass
            else:
                wait_t.destroy()
            cmd_log.flush()
            #tkMessageBox.showinfo("Complete!", "get file:\n %s \n Complete!" % re_file)
        else:
            tl = Toplevel()
            tl.attributes("-topmost", 1)
            tl.title("ERROR:get file %s --> %s (%s)\n" % (re_file,lo_file,datetime.now()))
            err_text = Label(tl, bg='black', fg='red',width=100, height=10, text="ERROR:There is no file name or path name!")
            err_text.pack(fill=BOTH)


    def send_ui():
        global sendfile_top
        sendfile_top = Toplevel()
        sendfile_top.attributes("-topmost", 1)
        sendfile_top.title("send file")

        send_remote = Label(sendfile_top, text="remote file:")
        send_remote.grid(row=0, column=0)
        global send_re
        send_re = Entry(sendfile_top, insertbackground='green', width=50)
        send_re.grid(row=0, column=1)
        def send_file_select():
            send_filename=askopenfilename()
            send_lo.delete(0, END)
            send_lo.insert(END,send_filename)
            send_re.delete(0,END)
            send_re.insert(END,"/tmp/"+os.path.split(send_filename)[-1])
        send_select_but=Button(sendfile_top,text='...',command=send_file_select)
        send_select_but.grid(row=1,column=2)
        send_locate = Label(sendfile_top, text="local file:")
        send_locate.grid(row=1, column=0)
        global send_lo
        send_lo = Entry(sendfile_top, insertbackground='green', width=50)
        send_lo.grid(row=1, column=1)
        sendfile_sub_but = Button(sendfile_top, text='send', command=send_file)
        sendfile_sub_but.grid(row=2)
    def send_file():
        try:
            thread_num=int(thread_num_entry.get())
        except:
            thread_num=int(10)
        semaphore= Semaphore(thread_num)
        def send_do(i,lo_file,re_file,FileSend):
            if semaphore.acquire():
                gl.server_all[i].FileTransfer(lo_file=lo_file,re_file=re_file,FileSend=FileSend)
            semaphore.release()
        re_file=send_re.get()
        lo_file=send_lo.get()
        if re_file and lo_file:
            try:
                gl.thread_num=int(thread_num_entry.get())
            except:
                gl.thread_num=int(10)
            save_log(log='%s    send file: %s --> %s \n' % (datetime.now(), lo_file, re_file))
            threads = []
            wait_t = Toplevel()
            wait_t.attributes("-topmost", 1)
            wait_t.title("Send file:%s --> %s" % (lo_file, re_file))
            w_text = Text(wait_t, bg='black', fg='green')
            w_scroll = Scrollbar(wait_t, command=w_text.yview)
            w_text.configure(yscrollcommand=w_scroll.set)
            w_scroll.pack(side=RIGHT, fill=Y)
            w_text.pack(fill=BOTH,expand=YES)
            sleep(0.02)
            root.update()
            clear()
            sendfile_top.destroy()
            for i in gl.server_all.keys():
                if gl.server_all[i].selected.get() == 1:
                    w_text.insert(END,'%s\n' % i)
                    a = Thread(target=send_do,kwargs={'i':i,'lo_file':lo_file,'re_file':re_file,'FileSend':1},name=i)
                    a.start()
                    threads.append(a)
                    sleep(0.02)
                    root.update()
            while True:
                for a in threads:
                    sleep(0.02)
                    root.update()
                    if not a.isAlive():
                        sleep(0.02)
                        root.update()
                        if gl.server_all[a.getName()].err:
                            gl.cbuts[a.getName()]['foreground'] = "red"
                            try:
                                where = w_text.search('%s\n' % a.getName(), '0.0', END)
                                if where:
                                    pastit = where + ('+%dc' % (len(a.getName())+1))
                                    w_text.delete(where, pastit)
                            except:
                                pass
                            try:
                                err_text.insert(END, "--------------------------------------%s\n" % a.getName())
                                save_log(log="--------------------------------------%s\n" % a.getName())
                                err_text.insert(END, gl.server_all[a.getName()].err)
                                save_log(log=gl.server_all[a.getName()].err)
                                err_text.see(END)
                                gl.server_all[a.getName()].err = ''
                                sleep(0.02)
                                root.update()
                            except:
                                tl = Toplevel()
                                tl.attributes("-topmost", 1)
                                tl.title("ERROR:send file %s --> %s (%s)\n" % (lo_file,re_file,datetime.now()))
                                err_text = Text(tl, bg='black', fg='red')
                                err_scroll = Scrollbar(tl, command=err_text.yview)
                                err_text.configure(yscrollcommand=err_scroll.set)
                                err_scroll.pack(side=RIGHT, fill=Y)
                                err_text.pack(fill=BOTH,expand=YES)
                                err_text.insert(END, "--------------------------------------%s\n" % a.getName())
                                save_log(log="--------------------------------------%s\n" % a.getName())
                                err_text.insert(END, gl.server_all[a.getName()].err)
                                save_log(log=gl.server_all[a.getName()].err)
                                err_text.see(END)
                                gl.server_all[a.getName()].err = ''
                                sleep(0.02)
                                root.update()
                            threads.remove(a)
                        elif gl.server_all[a.getName()].send_file_status:
                            try:
                                where = w_text.search('%s\n' % a.getName(), '0.0', END)
                                pastit = where + ('+%dc' % (len(a.getName())+1))
                                w_text.delete(where, pastit)
                            except:
                                pass
                            text.insert(END, "--------------------------------------%s\n" % a.getName())
                            save_log(log="--------------------------------------%s\n" % a.getName())
                            text.insert(END, "send file %s --> %s %s\n" % (lo_file, re_file, gl.server_all[a.getName()].send_file_status))
                            save_log(log="send file %s --> %s %s\n" % (lo_file, re_file, gl.server_all[a.getName()].send_file_status))
                            gl.server_all[a.getName()].result = ''
                            sleep(0.02)
                            root.update()
                            threads.remove(a)
                if not threads:
                    break

            text.insert(END, "######################all the servers finished send file:%s --> %s (%s)\n" % (lo_file,re_file,datetime.now()))
            save_log(log="######################all the servers finished send file:%s --> %s (%s)\n" % (lo_file,re_file,datetime.now()))
            if w_text.get(0.0, END).split():
                pass
            else:
                wait_t.destroy()
            cmd_log.flush()
            #tkMessageBox.showinfo("Complete!", "send file:\n %s \n Complete!" % lo_file)
        else:
            tl = Toplevel()
            tl.attributes("-topmost", 1)
            tl.title("ERROR:send file %s --> %s (%s)\n" % (lo_file,re_file,datetime.now()))
            err_text = Label(tl, bg='black', fg='red',width=100, height=10, text="ERROR:There is no file name or path name!")
            err_text.pack(fill=BOTH)

    # gui
    class AutocompleteCombobox(Combobox):
        def set_completion_list(self, completion_list):
            """Use our completion list as our drop down selection menu, arrows move through menu."""
            self._completion_list = sorted(completion_list, key=str.lower)  # Work with a sorted list
            self._hits = []
            self._hit_index = 0
            self.position = 0
            self.bind('<KeyRelease>', self.handle_keyrelease)
            self['values'] = self._completion_list  # Setup our popup menu
        def autocomplete(self, delta=0):
            if delta:
                    self.delete(self.position, END)
            else:
                    self.position = len(self.get())
            _hits = []
            for element in self._completion_list:
                    if element.lower().startswith(self.get().lower()):
                            _hits.append(element)
            if _hits != self._hits:
                    self._hit_index = 0
                    self._hits = _hits
            if _hits == self._hits and self._hits:
                    self._hit_index = (self._hit_index + delta) % len(self._hits)
            if self._hits:
                    self.delete(0, END)
                    self.insert(0, self._hits[self._hit_index])
                    self.select_range(self.position, END)

        def handle_keyrelease(self, event):
    #         if event.keysym == "BackSpace":
    #                 self.delete(self.index(INSERT), END)
    #                 self.position = self.index(END)
    #         if event.keysym == "Left":
    #                 if self.position < self.index(END):
    #                         self.delete(self.position, END)
    #                 else:
    #                         self.position = self.position - 1
    #                         self.delete(self.position, END)
            if event.keysym == "Right":
                    self.position = self.index(END)
            if len(event.keysym) == 1:
                    self.autocomplete()
    class FullScreenApp(object):
        def __init__(self, master, **kwargs):
            self.root = master
            # self.tk.attributes('-zoomed', True)  # This just maximizes it so we can see the window. It's nothing to do with fullscreen.
            self.frame = Frame(self.root)
            self.frame.pack()
            self.state = False
            self.root.bind("<F11>", self.toggle_fullscreen)
            self.root.bind("<Escape>", self.end_fullscreen)

        def toggle_fullscreen(self, event=None):
            self.state = not self.state  # Just toggling the boolean
            self.root.attributes("-fullscreen", self.state)
            return "break"

        def end_fullscreen(self, event=None):
            self.state = False
            self.root.attributes("-fullscreen", False)
            return "break"
    root = Tk()
    def close_all():
        for i in gl.server_all.keys():
            if gl.server_all[i].connect_status:
                gl.server_all[i].close()
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", close_all)
    root.option_add('*background', 'black')
    root.option_add('*foreground', 'green')
    root.title('jssh')
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
        print 'system type is not supported'
    if os.path.isfile(gl.history_file):
        pass
    else:
        open(gl.history_file,'w').write('''(lp1
S'df -h'
p2
aS'ifconfig'
a.
''')
    #root.iconbitmap(default='jssh.ico')
    # 菜单栏
    def open_logfile():
        #os.system('notepad %s' % gl.logfile)
        tl = Toplevel()
        tl.title("Log")
        log_text = Text(tl, bg='black', fg='green')
        log_scroll = Scrollbar(tl, command=log_text.yview)
        log_text.configure(yscrollcommand=log_scroll.set)
        log_scroll.pack(side=RIGHT, fill=Y)
        log_text.pack(fill=BOTH,expand=YES)
        log=file(gl.logfile)
        for i in log:
            log_text.insert(END, i)
        log_text.see(END)
        log.close()

    def help():
        help_msg = '''
    You should create server-list file frist:
                 formate：hostname ip:port username password
                 eg：hostname 192.168.1.10:22 root password
                 use utf-8 formate better，one server one line
    Use Ctrl + left-click a server that can be manipulated separately.
    Use right-click on a server you can find it in the results.
    F11 for full screen!
    '''
        ht = Toplevel()
        ht.attributes("-topmost", 1)
        hl = Label(ht, text=help_msg, justify="left").pack()

    menubar = Menu(root)
    menubar.add_command(label="send file",command=send_ui)
    menubar.add_command(label="get file", command=get_ui)
    menubar.add_command(label="log", command=open_logfile)
    menubar.add_command(label="help", command=help)
    menubar.add_command(label="exit", command=close_all)
    root.config(menu=menubar)
    # 命令窗口
    command_frame = Frame(root, bd=1, relief=SUNKEN)
    command_frame.pack(side=TOP, fill=X)
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
    entry = AutocompleteCombobox(command_frame)
    entry.set_completion_list(gl.history_cmd)
    entry.pack(fill=X)

    # 确认按键
    command_but = Button(command_frame, text='OK', state=DISABLED, command=gexe_cmd)
    command_but.pack(side=RIGHT)
    # 打开文件按键
    file_but = Button(command_frame, text='select server list', command=open_list)
    file_but.pack(side=LEFT)
    # 执行返回结果框及进度条
    text_frame = Frame(root, bd=2, relief=SUNKEN)
    text_frame.pack(side=RIGHT, fill=BOTH,expand=YES)
    text = Text(text_frame, insertbackground='green', fg='green')
    scroll = Scrollbar(text_frame, command=text.yview)
    text.configure(yscrollcommand=scroll.set)
    scroll.pack(side=RIGHT, fill=Y)
    text.pack(fill=BOTH,expand=YES)
    # 服务器列表
    server_frame = Frame(root, bd=2, relief=SUNKEN)
    server_frame.pack(side=LEFT, fill=Y)
    def select_all():
        for i in gl.cbuts.keys():
             gl.cbuts[i].select()
    def deselect_all():
        for i in gl.cbuts.keys():
             gl.cbuts[i].deselect()
    def select_con():
        for i in gl.cbuts.keys():
            if gl.server_all[i].connect_status:
                gl.cbuts[i].select()
            else:
                gl.cbuts[i].deselect()
    def deselect_reverse():
        for i in gl.cbuts.keys():
            if gl.server_all[i].selected.get() == 1:
                gl.cbuts[i].deselect()
            else:
                gl.cbuts[i].select()
    server_all_frame = Frame(server_frame, bd=2, relief=SUNKEN)
    server_all_frame.pack(side=TOP)
    Button(server_all_frame, text='all', command=select_all).grid(row=0, column=0,sticky='nesw')
    Button(server_all_frame, text='none', command=deselect_all).grid(row=0, column=1,sticky='nesw')
    Button(server_all_frame, text='just_connected', command=select_con).grid(row=1, column=0,sticky='nesw')
    Button(server_all_frame, text='reverse', command=deselect_reverse).grid(row=1, column=1,sticky='nesw')
    ft = Font(family='Fixdsys', size=11, weight=NORMAL, underline=1)

    def listfunction(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    server_list_frame = Frame(server_frame, bd=2, relief=SUNKEN)
    server_list_frame.pack(fill=Y,expand=YES)

    canvas = Canvas(server_list_frame, width=150, height=500)
    listframe = Frame(canvas)
    myscrollbar = Scrollbar(server_list_frame, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=myscrollbar.set)
    myscrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill=Y)
    canvas.create_window((0, 0), window=listframe)
    listframe.bind("<Configure>", listfunction)


    # 连接断开按键
    connect = Button(command_frame, text='connect', state=DISABLED, command=connect)
    connect.pack(side=LEFT)
    disconnect = Button(command_frame, text='disconnect', state=DISABLED, command=disconnect)
    disconnect.pack(side=LEFT)
    #线程数量限制
    thread_num_label = Label(command_frame,text='    Max Threads: ')
    thread_num_label.pack(side=LEFT)
    thread_num_e = StringVar()
    thread_num_entry = Entry(command_frame,textvariable=thread_num_e,width=5,insertbackground = 'green')
    thread_num_e.set('10')
    thread_num_entry.pack(side=LEFT)
    # 鼠标右键
    def save():
        save_file = asksaveasfilename(initialdir='.')
        if save_file:
            open(save_file, 'w').write(text.get(0.0, END))
    
    def clear():
        text.delete('0.0', END)
    menubar = Menu(root)
    menubar.add_command(label='save', command=save)
    menubar.add_command(label='clear', command=clear)
    def popup(event):  # 显示菜单    
        menubar.post(event.x_root, event.y_root) 
    text.bind('<Button-3>', popup)
    cmd_log = open(gl.logfile, 'a')
    def save_log(log=''):
        cmd_log.write(log)
    def the_end():
        # cmd_log.close()
        print 'the end'
    signal(SIGTERM, the_end)
    signal(SIGINT, the_end)
    root.mainloop()
if __name__=='__main__':
    main()
