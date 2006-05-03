#!/usr/bin/env python
# Michael DeHaan <mdehaan@redhat.com>

"""
Command line interface for BootConf, a network boot configuration
library
"""

import os
import sys
import api
from msg import *

class BootCLI:


    def __init__(self,args):
        """
        Build the command line parser and API instances, etc.
        """
        self.args = args
        self.api = api.BootAPI()
        self.commands = {}
        self.commands['distro'] = { 
            'add'     :  self.distro_edit,
            'edit'    :  self.distro_edit,
            'delete'  :  self.distro_remove,
            'remove'  :  self.distro_remove,
            'list'    :  self.distro_list
        }
        self.commands['profile'] = {
            'add'     :  self.profile_edit,
            'edit'    :  self.profile_edit,
            'delete'  :  self.profile_remove,
            'remove'  :  self.profile_remove,
            'list'    :  self.profile_list
        }
        self.commands['system'] = {
            'add'     :  self.system_edit,
            'edit'    :  self.system_edit,
            'delete'  :  self.system_remove,
            'remove'  :  self.system_remove,
            'list'    :  self.system_list
        }
        self.commands['toplevel'] = {
            'check'    : self.check,
            'distros'  : self.distro,
            'distro'   : self.distro,
            'profiles' : self.profile, 
            'profile'  : self.profile, 
            'systems'  : self.system,
            'system'   : self.system,
            'sync'     : self.sync,
            '--help'   : self.usage,
            '/?'       : self.usage
        }


    def run(self):
        """
        Run the command line
        """
        rc = self.curry_args(self.args[1:], self.commands['toplevel'])
        if not rc:
            print self.api.last_error
        return rc


    def usage(self,args):
        """
        Print out abbreviated help if user gives bad syntax
        """
        print m("usage")
        return False


    def system_list(self,args):
        """
        Print out the list of systems:  '$0 system list'
        """
        print str(self.api.get_systems())


    def profile_list(self,args):
        """
        Print out the list of profiles: '$0 profile list'
        """
        print str(self.api.get_profiles())
    

    def distro_list(self,args):
        """
        Print out the list of distros: '$0 distro list'
        """
        print str(self.api.get_distros())


    def system_remove(self,args):
        """
        Delete a system:  '$0 system remove --name=foo'
        """
        commands = {
           '--name'       : lambda(a):  self.api.get_systems().remove(a) 
        }
        on_ok = lambda: True
        return self.apply_args(args,commands,on_ok,True)


    def profile_remove(self,args):
        """
        Delete a profile:   '$0 profile remove --name=foo'
        """
        commands = {
           '--name'       : lambda(a):  self.api.get_profiles().remove(a)
        }
        on_ok = lambda: True
        return self.apply_args(args,commands,on_ok,True)


    def distro_remove(self,args):
        """
        Delete a distro:  '$0 distro remove --name='foo'
        """
        commands = {
           '--name'     : lambda(a):  self.api.get_distros().remove(a)
        }
        on_ok = lambda: True
        return self.apply_args(args,commands,on_ok,True)


    def system_edit(self,args):
        """
        Create/Edit a system:  '$0 system edit --name='foo' ...
        """
        sys = self.api.new_system()
        commands = {
           '--name'     :  lambda(a) : sys.set_name(a),
           '--profile'  :  lambda(a) : sys.set_profile(a),    
           '--profiles' :  lambda(a) : sys.set_profile(a), # alias       
           '--kopts'    :  lambda(a) : sys.set_kernel_options(a)
        }
        on_ok = lambda: self.api.get_systems().add(sys)
        return self.apply_args(args,commands,on_ok,True)


    def profile_edit(self,args):
        """
        Create/Edit a profile:  '$0 profile edit --name='foo' ...
        """
        profile = self.api.new_profile()
        commands = {
            '--name'            :  lambda(a) : profile.set_name(a),
            '--distro'          :  lambda(a) : profile.set_distro(a),
            '--kickstart'       :  lambda(a) : profile.set_kickstart(a),
            '--kopts'           :  lambda(a) : profile.set_kernel_options(a),
            '--xen-name'        :  lambda(a) : profile.set_xen_name(a),
            '--xen-file-size'   :  lambda(a) : profile.set_xen_file_size(a),
            '--xen-ram'         :  lambda(a) : profile.set_xen_ram(a),
            '--xen-mac'         :  lambda(a) : profile.set_xen_mac(a),
            '--xen-paravirt'    :  lambda(a) : profile.set_xen_paravirt(a),
            # FIXME: more Xen opts that xen-guest-install needs
        }
        on_ok = lambda: self.api.get_profiles().add(profile)
        return self.apply_args(args,commands,on_ok,True)
    

    def distro_edit(self,args):
        """
        Create/Edit a distro:  '$0 distro edit --name='foo' ...
        """
        distro = self.api.new_distro()
        commands = {
            '--name'      :  lambda(a) : distro.set_name(a),
            '--kernel'    :  lambda(a) : distro.set_kernel(a),
            '--initrd'    :  lambda(a) : distro.set_initrd(a),
            '--kopts'     :  lambda(a) : distro.set_kernel_options(a)
        }
        on_ok = lambda: self.api.get_distros().add(distro)
        return self.apply_args(args,commands,on_ok,True)


    def apply_args(self,args,input_routines,on_ok,serialize):
        """
        Instead of getopt...
        Parses arguments of the form --foo=bar, see profile_edit for example
        """
        if len(args) == 0:
            print m("no_args")
            return False
        for x in args:
            try:
                key, value = x.split("=",1)
                value = value.replace('"','').replace("'",'')
            except:
                print m("bad_arg") % x
                return False
            if key in input_routines:
                if not input_routines[key](value):
                   print m("reject_arg") % key
                   return False
            else:
                print m("weird_arg") % key
                return False
        rc = on_ok()
        if rc and serialize:
            self.api.serialize()
        return rc


    def curry_args(self, args, commands):
        """
        Helper function to make subcommands a bit more friendly.
        See profiles(), system(), or distro() for examples
        """
        if args is None or len(args) == 0:
            print m("help")
            return False
        if args[0] in commands:
            rc = commands[args[0]](args[1:])
            if not rc:
               return False
        else:
            print m("unknown_cmd") % args[0]
            return False
        return True


    def sync(self, args):
        """
        Sync the config file with the system config: '$0 sync [--dryrun]'
        """
        status = None 
        if args is not None and "--dryrun" in args:
            status = self.api.sync(dry_run=True)
        else:
            status = self.api.sync(dry_run=False)
        return status
       

    def check(self,args):
        """
        Check system for network boot decency/prereqs: '$0 check'
        """
        status = self.api.check()
        if status is None:
            return False
        elif len(status) == 0:
            print m("check_ok")
            return True
        else:
            print m("need_to_fix")
            for i,x in enumerate(status): 
               print "#%d: %s" % (i,x)
            return False
  

    def distro(self,args):
        """
        Handles any of the '$0 distro' subcommands
        """
        return self.curry_args(args, self.commands['distro']) 


    def profile(self,args):
        """
        Handles any of the '$0 profile' subcommands
        """
        return self.curry_args(args, self.commands['profile'])


    def system(self,args):
        """
        Handles any of the '$0 system' subcommands
        """
        return self.curry_args(args, self.commands['system'])

def main():
    if os.getuid() != 0: # FIXME
       print m("need_root")
       sys.exit(1)
    if BootCLI(sys.argv).run():
       sys.exit(0)
    else:
       sys.exit(1)
