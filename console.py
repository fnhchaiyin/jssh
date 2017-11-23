import readline
import rlcompleter
readline.parse_and_bind('tab: complete')
commands=['execcmd','sendfile','getfile','server_list']
class TabCompleter(rlcompleter.Completer):
    """Completer that supports indenting"""
    def complete(self, text, state):
        if not text:
            return ('    ', None)[state]
        else:
            print 'text:',type(text),text
            print 'state:',type(state),state
            return rlcompleter.Completer.complete(self, text, state)

readline.set_completer(TabCompleter().complete)
while True:
    input=raw_input('>')
    print input
