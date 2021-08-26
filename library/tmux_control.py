#!/usr/bin/python3

ANSIBLE_METADATA = {
    'metadata_version': '0.0.0.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''

---
module: tmux_control

short_description: Allows for manipulation of a tmux server

description:
    - "Allows for manipulation of a tmux server

author:
    - Matthew Cundari (chashtag)
'''

EXAMPLES = '''
- tmux_control:
        session_name: tester
        window_name: tester
        remain_on_exit: yes
        set_active: yes
        send_keys:
          - echo asd
          - echo `echo backtick test`
          - sleep 3
          - echo qwe
'''

RETURN = '''
nothing right now
'''

from ansible.module_utils.basic import AnsibleModule
import subprocess as sp



def run_module():
    module_args = dict(
        session_name=dict(type='str', required=True),
        window_name=dict(type='str', required=False),
        remain_on_exit=dict(type='bool', required=False, default=None),
        send_keys=dict(type='list', required=False, default=False),
        state=dict(type='str', required=False, default='present'),
        set_active=dict(type='bool', required=False, default=False),
        cmd=dict(type='list', required=False),

    )
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    result = dict(
        changed=False,
        original_message='',
        message='asd',
        commands=[]
    )
    
    #TODO: handle fail if no tmux
    _TPATH = sp.check_output(['/usr/bin/command','-v','tmux']).strip().decode('utf-8')
    
    
    #module.fail_json(msg=result.text,**result)
    def do_tmux(cmds:list):
        if type(cmds) != list:
            raise Exception('cmds arg must be in list format')
        else:
            cmds = [_TPATH]+cmds
        
        #TODO: clean this up, only if verbose maybe
        result['commands'].append(' '.join(cmds))

        ret = sp.run(cmds,capture_output=True)
    
        result['stderr'] = str(ret.stderr)
        result['stdout'] = str(ret.stdout)
        
        return ret.stdout.decode('utf-8')
    

    def is_server_running():
        ret = do_tmux(['ls']) #TODO: tots can do this better
        return ret


    def get_windows():
        _d = {}
        if is_server_running():
            ret = do_tmux([
                'list-windows',
                '-F',
                '#S:::#W']) #TODO: get pane status ie. :::#{?pane_dead,yes,no}
            if ret:
                for x in ret.split('\n'):
                    if ':::' in x:
                        a = x.split(':::')
                        if a[0] in _d:
                            _d[a[0]].append(a[1])
                        else:
                            _d.update({a[0]:[a[1]]})
        return _d
        

    def make_wind_name():
        if module.params['window_name']:
            _wind = ':'.join([module.params['session_name'],module.params['window_name']])
        else:
            _wind = module.params['session_name']
        return _wind


    def kill():
        cmds = []
        if is_server_running():
            _windows = get_windows()
            result['messagea'] = _windows
        
        if _windows.get(module.params['session_name'],False):
            if module.params['window_name']:
                cmds.extend(['kill-window',
                             '-t',
                             ':'.join([module.params['session_name'],module.params['window_name']])] )
                             
            else:
                cmds.extend(['kill-session',
                             '-t',
                             module.params['session_name']])
        if cmds:
            do_tmux(cmds)
            result['changed'] = True
            cmds = []
        

    def spawn():
        cmds = []
        create_window = False
        if is_server_running():
            _windows = get_windows()
            result['messagea'] = _windows
            
            if not _windows.get(module.params['session_name'],False):
                cmds.extend(['new-session','-d','-s',module.params['session_name']])
                create_window = True
                
            elif module.params['window_name'] and not module.params['window_name'] in _windows.get(module.params['session_name'],[]):
                cmds.extend(['new-window','-d','-t',module.params['session_name'],'-n',module.params['window_name']])
                create_window = True
        
        else:
            cmds.extend(['new-session','-d','-s',module.params['session_name']])
        
            if module.params['window_name']:
                cmds.extend(['-n',module.params['window_name']])

            create_window = True
        
        if create_window:  
            do_tmux(cmds)
            result['changed'] = True
            cmds = []


    if module.params['state'] == 'present' or module.params['state'] == 'restarted':
        cmds = []
        if module.params['state'] == 'restarted':
            kill()
        spawn()
            
        if module.params['remain_on_exit'] != None:
            cmds.extend(['set-window-option',
                        '-t',
                        make_wind_name(),
                        'remain-on-exit', 
                        'on' if module.params['remain_on_exit'] else 'off'
                        ])
            
            do_tmux(cmds)
            result['changed'] = True
            cmds = []

        if module.params['set_active']:
            cmds.extend(['select-window',
                        '-t',
                        make_wind_name()
                        ])
            
            do_tmux(cmds)
            result['changed'] = True
            cmds = []

        if module.params['send_keys']:
            for line in module.params['send_keys']:
                line = line.replace("'","\\'")
                cmds = ['send-keys',
                        '-t',
                        make_wind_name(),
                        line,
                        'Enter'
                        ]
                do_tmux(cmds)
                result['changed'] = True
            cmds = []

    elif module.params['state'] == 'absent':
        kill()
        
    else:
        result['message'] = 'what??'
    
    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()