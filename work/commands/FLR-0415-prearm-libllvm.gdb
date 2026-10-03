set pagination off
set height 0
set width 0
set confirm off
set breakpoint always-inserted on
catch load libLLVM\.so\.18\.1
commands 1
silent
python
import gdb, os, re, struct
root='/run/user/1001/flr0415-0001'
try:
 path='/usr/lib/libLLVM.so.18.1'; vma=0xb1d541
 expected='359c1108040bc6bc1af64bb639d0b25385858051'
 f=open(path,'rb'); header=f.read(64)
 if header[:6]!=b'\x7fELF\x02\x01': raise RuntimeError('unexpected ELF class/encoding')
 phoff=struct.unpack_from('<Q',header,32)[0]
 entsize,count=struct.unpack_from('<HH',header,54); seg=[]; build=''
 for i in range(count):
  f.seek(phoff+i*entsize); h=f.read(entsize)
  t,fl,off,va,pa,fs,ms,al=struct.unpack_from('<IIQQQQQQ',h)
  if t==1 and fl&1 and va<=vma<va+ms: seg.append((off,va,ms))
  if t==4:
   f.seek(off); notes=f.read(fs); z=0; end=len(notes)
   while z+12<=end:
    ns,ds,nt=struct.unpack_from('<III',notes,z); z+=12
    name=notes[z:z+ns].rstrip(b'\0'); z=(z+ns+3)&~3
    desc=notes[z:z+ds]; z=(z+ds+3)&~3
    if name==b'GNU' and nt==3: build=desc.hex()
 f.close()
 if build!=expected or len(seg)!=1: raise RuntimeError('ELF Build-ID/PT_LOAD mismatch')
 pid=gdb.selected_inferior().pid; page=os.sysconf('SC_PAGE_SIZE'); hits=[]
 for line in open('/proc/%d/maps'%pid):
  f=line.split(None,5)
  if len(f)<6 or f[5].strip()!=path or 'x' not in f[1]: continue
  a,b=(int(x,16) for x in f[0].split('-')); mo=int(f[2],16); po,va,ms=seg[0]
  bias=a-(va//page*page)-(mo-po//page*page); addr=bias+vma
  if a<=addr<b and mo+addr-a==po+vma-va: hits.append((addr,bias,line.strip()))
 if len(hits)!=1: raise RuntimeError('unique executable mapping not proven')
 addr,bias,mapping=hits[0]; status=open('/proc/%d/status'%pid).read()
 uid=int(re.search(r'^Uid:\s+(\d+)',status,re.M).group(1))
 tail=open('/proc/%d/stat'%pid).read().rsplit(')',1)[1].split(); start=tail[19]
 if uid!=1001: raise RuntimeError('inferior UID mismatch')
 out=gdb.execute('hbreak *0x%x'%addr,to_string=True)
 m=re.search(r'Hardware assisted breakpoint (\d+) at',out)
 if not m: raise RuntimeError('hardware insertion unconfirmed: '+out)
 number=m.group(1)
 with open(root+'-identity','x') as f: f.write('%d %d %s\n'%(pid,uid,start))
 with open(root+'-armed','x') as f: f.write('pid=%d uid=%d start=%s build_id=%s vma=0x%x bias=0x%x address=0x%x map=%s\n'%(pid,uid,start,build,vma,bias,addr,mapping))
 gdb.write('FLR0415_HWB_INSERTION='+out)
 commands='commands %s\nsilent\nprintf "FLR0415_HIT_PC=%%p\\n", $pc\ninfo threads\ninfo registers rip r10 rsp eflags cs ss\nx/16bx $pc-8\nx/8i $pc-4\nbt 16\nx/8gx $rsp\npython\nopen("%s-hit","x").write("pid=%d start=%s pc=0x%%x" %% (gdb.selected_inferior().pid, gdb.selected_frame().pc()))\nend\nend'%(number,root,pid,start)
 gdb.execute(commands); gdb.write('FLR0415_LIBLLVM_CATCH=PASS build_id=%s map=%s address=0x%x\n'%(build,mapping,addr))
except Exception as error:
 with open(root+'-failure','x') as f: f.write(repr(error)+'\n')
 gdb.execute('kill')
 raise
end
continue
end
run
python
import gdb, os, time
root='/run/user/1001/flr0415-0001'
if not os.path.exists(root+'-hit'):
 with open(root+'-stop','x') as f: f.write(gdb.execute('info program',to_string=True))
deadline=time.monotonic()+60
while not os.path.exists(root+'-release') and time.monotonic()<deadline: time.sleep(0.1)
if not os.path.exists(root+'-release'): gdb.write('FLR0415_RELEASE=TIMEOUT\n')
end
kill
