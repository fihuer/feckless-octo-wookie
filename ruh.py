#!/bin/env python
# -*- coding: utf-8 -*-

#### Imports ####

import cmd
import sys
import shlex
import ConfigParser
import os.path

# Custom lib
import wookieLib
from wookieLib import OptionParser, OptionGroup, Option
import expressions

#### Globals ####

#### Classes ####

class InteractiveOrCommandLine(cmd.Cmd):
    """Accepts commands via the normal interactive prompt or on the command line."""

    def do_greet(self, line):
        print type(line)
        print 'hello', line
    
    def do_EOF(self, line):
        return True

    def do_parse(self, line):
        """Parses and prints (in a pager if big enough) 
        cached or newly compile catalog"""
        usage = "usage: %prog parse [options]"
        parser = OptionParser(usage=usage)
        parser.add_option("-f", "--file", dest="catalogPath", default=None,
                          help="parse catalog located at FILE", metavar="FILE")
        parser.add_option("-c", "--compile", dest="compile",default=False,
                          help="Compile a new catalog instead of the cached one",
                          action="store_true")
        (options, args) = parser.parse_args(shlex.split(line))
        if options.compile:
            raise NotImplementedError
        elif options.catalogPath:
            thread = parse_catalog(options.catalogPath)
            result, ftype = thread.result_queue.get()
            wookieLib.politePrint(ftype.dumps(result, indent=4))
        else:
            raise NotImplementedError
        
    def do_config(self, line):
        """Prints one or several values of the Puppet config
        list: list all the values (puppet config print)
        print: print asked values
        """
        usage = "usage: %prog config [list|print] [args]"
        parser = OptionParser(usage=usage)
        (options, args) = parser.parse_args(shlex.split(line))
        if len(args) < 1:
            parser.print_help()
        elif args[0]=="print" and len(args) >= 2:
            for arg in args[1:]:
                print arg,"=",PUPPET.get(arg)
        elif args[0]=="list":
            for item,value in PUPPET.items():
                print item,"=",value

    def do_find(self, line):
        """
Find-like function to filter a catalog.
Currently implemented expressions will be described underneath
        """
        usage = self.do_find.__doc__+"\nusage: %prog find [options] expression"
        parser = OptionParser(usage=usage)
        parser.add_option("-f", "--file", dest="catalogPath", default=None,
                          help="parse catalog located at FILE", metavar="FILE")
        parser.add_option("-c", "--compile", dest="compile",default=False,
                          help="Compile a new catalog instead of the cached one",
                          action="store_true")
        parser.add_option("--dump", dest="dump",default=False,
                          help="Dump result in stdout (not a pager)",
                          action="store_true")

        group, expr_objs = expressions.defineExpressions(parser)
        parser.add_option_group(group)
        (options, args) = parser.parse_args(shlex.split(line))
        if options.compile:
            raise NotImplementedError
        elif options.catalogPath:
            thread = parse_catalog(options.catalogPath)
        filterMap = {}
        for exp in expr_objs:
            value = getattr(options, exp.paramName)
            if value:
                filterMap[exp.paramName] = [value, exp]
        catalog, ftype = thread.result_queue.get()
        filteredCatalog = filterCatalog(catalog, filterMap, expr_objs)
        if options.dump:
            print ftype.dumps(filteredCatalog, indent=4)
        else:
            wookieLib.politePrint(ftype.dumps(filteredCatalog, indent=4))
        
class Puppet(object):
    def __init__(self):
        self.configThread = parse_puppet_config()
        self._config = None
        
    @property
    def config(self):
        if not self._config:
            self._config = self.configThread.result_queue.get()
        return self._config

    def __getitem__(self, attr):
        self.get(attr)

    def get(self, attr):
        try:
            return self.config.get("puppet", attr)
        except ConfigParser.NoOptionError:
            pass

    def items(self):
        return self.config.items("puppet")
        
#### Defines ####

@wookieLib.threaded
def parse_catalog(location, fd=None, ftype='json'):
    if fd:
        extension = ftype
    else:
        extension = os.path.splitext(location)[1].split('.')[1]

    m = __import__(extension)
    if fd:
        catalog = m.loads(fd.read())
    else:
        with open(location) as f:
            catalog = m.loads(f.read())
    return catalog, m

@wookieLib.threaded
def parse_puppet_config():
    import StringIO
    from subprocess import check_output
    ini_str = "[puppet]\n"+check_output(["puppet", "config", "print"])
    ini_fp = StringIO.StringIO(ini_str)
    config = ConfigParser.RawConfigParser()
    config.readfp(ini_fp)
    return config

# def defineExpressions(parser):
#     group = OptionGroup(parser, "Expressions",
#                         "Use expression to filter out items from catalogs")
#     expressions = []
#     expressions.append(["-type",Option("-type", help="Ressource type", dest="type")])
#     expressions.append(["-title",Option("-title", help="Ressource title", dest="title")])
#     for expr in expressions:
#         group.add_option(expr[1])
#     return group, [exp[0] for exp in expressions ]

def filterCatalog(catalog, filterMap, expr_objs):
    res = []
    for resource in catalog["data"]["resources"]:
        if filterHit(resource, filterMap, expr_objs):
            res.append(resource)
    return res

def filterHit(item, filterMap, expr_objs):
    hit = True
    touched = False
    for key, fobj in filterMap.iteritems():
        expr = fobj[1]
        values = fobj[0]
        for value in values:
            if expr.name in item:
                if expr.compare(item[expr.name],expr.normalize(value)):
                    touched = True
                    hit = hit and True
                else:
                    touched = True
                    hit = hit and False
            else:
                pass
    if touched:
        return hit
    else:
        return False

def getExpr(key, expr_objs):
    for expr in expr_objs:
        if key == expr.paramName:
            return expr
    return None
#### Main    ####

if __name__ == '__main__':
    global PUPPET
    PUPPET = Puppet()
    if len(sys.argv) > 1:
        InteractiveOrCommandLine().onecmd(' '.join(sys.argv[1:]))
    else:
        InteractiveOrCommandLine().cmdloop()
