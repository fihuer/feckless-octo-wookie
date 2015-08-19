#!/bin/env python
# -*- coding: utf-8 -*-

#### Imports ####
import re
from wookieLib import Option, OptionGroup
#### Globals #### 

#### Classes ####
class Expression (object):
    def __init__(self, name, description, append=True, paramName=None):
        self.name = name
        self.description = description
        self.append=True
        if paramName:
            self.paramName=paramName
        else:
            self.paramName=self.name

    @property
    def option(self):
        if self.append:
            return Option("-"+self.paramName, help=self.description, dest=self.paramName, action="append")
        else:
            return Option("-"+self.paramName, help=self.description, dest=self.paramName, action="store")   

    def normalize(self, value):
        #Nothing to do by default
        return value

    def compare(self, is_value, wanted_value):
        return is_value == self.normalize(wanted_value)


class CapitalizeExpr(Expression):
    def normalize(self, value):
        return str(value).capitalize()

class ArrayExpr(Expression):
    def compare(self, is_value, wanted_value):
        # print is_value, wanted_value
        # print wanted_value in is_value
        return wanted_value in is_value

class ParamExpr(Expression):
    def compare(self, is_value, wanted_value):
        splt = wanted_value.split("=")
        name = str(splt[0])
        value = str(splt[1])
        if name in is_value:
            try:
                casted = type(is_value[name])(value)
            except TypeError:
                return self.normalize(is_value[name]) == value
            return self.normalize(is_value[name]) == casted
        else:
            return False

class RequireExpr(Expression):
    def compare(self, is_value, wanted_value):
        requires = is_value.get("require",[])
        # print requires, self.normalize(wanted_value)
        return self.normalize(wanted_value) in requires

class RegexExpr(Expression):
    def __init__(self, name, description, regexTmpl, append=True, paramName=None):
        super(RegexExpr, self).__init__(name, description, append, paramName)
        self.regexTmpl=str(regexTmpl)

    def compare(self, is_value, wanted_value):
        regex = self.regexTmpl.format(wanted_value)
        return bool(re.search(regex, is_value))

#### Defines ####
def defineExpressions(parser):
    group = OptionGroup(parser, "Expressions",
                        "Use expression to filter out items from catalogs")
    expressions = []
    expressions.append(CapitalizeExpr("type", "Ressource type", append=False))
    expressions.append(Expression("title", "Ressource title"))
    expressions.append(ArrayExpr("tags", "Ressource matches a given tag"))
    expressions.append(ParamExpr("parameters", "Ressource matches a given parameter"))
    expressions.append(RequireExpr("parameters", "Ressource requiring given ressources", paramName="requires"))
    expressions.append(RegexExpr("file", "Ressource matches a given tag", paramName="module", regexTmpl="/modules/{0}/"))

    for expr in expressions:
        group.add_option(expr.option)
        
    return group, expressions

####   Main  ####

if __name__ == '__main__':
    global PUPPET
    PUPPET = Puppet()
    if len(sys.argv) > 1:
        InteractiveOrCommandLine().onecmd(' '.join(sys.argv[1:]))
    else:
        InteractiveOrCommandLine().cmdloop()
