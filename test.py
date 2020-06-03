import os

path = os.path.join(os.curdir, "myNeatWebsite.url")
target = "http://www.google.com/"
with open(path, 'w') as shortcut:
    shortcut.write('[InternetShortcut]\n')
    shortcut.write('URL=%s' % target)
    shortcut.close()