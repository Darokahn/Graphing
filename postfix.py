from dataclasses import dataclass

class operators(float):
    @staticmethod
    def __neg__(arg):
        return -arg

class operator:
    opMap = {
            "+": "add",
            "-": "sub",
            "*": "mul",
            "/": "truediv",
            "div": "truediv",
            "^": "pow",
            "(": "(",
            ")": ")",
            "neg": "neg"
            }
    opBinary = "add", "sub", "mul", "truediv", "pow"
    opUnary = ("neg",)
    @classmethod
    def normalizeOp(cls, name):
        if not name in set(cls.opMap.keys()) | set(cls.opMap.values()):
            raise ValueError(f"invalid operation `{name}`.")
        if not name in cls.opMap:
            return name
        return cls.opMap[name]
    def __init__(self, name, opBank=operators):
        self.name = self.normalizeOp(name)
        self.binary = self.name in self.opBinary and not self.name in self.opUnary # redundant for explicit intention
        self.opBank = opBank
    def __call__(self, *args):
        return getattr(self.opBank, f"__{self.name}__")(*args)
    def __repr__(self):
        return f"{self.name}"
    def __str__(self):
        return repr(self)

def getFloat(string):
    val = None
    isFullFloat = False
    try:
        float(string)
        isFullFloat = True
    except Exception as e:
        pass # continue to partial check
    if isFullFloat:
        raise ValueError("cannot tell whether float is complete")
    try:
        val = float(string[:-1])
        return val
    except ValueError as e:
        raise e # make explicit that "error if unparseable as float" is intended behavior here.

class variable:
    def __init__(self, string):
        if string.isidentifier():
            raise ValueError("cannot tell whether name is complete")
        if not string[0:-1].isidentifier():
            raise ValueError("not a valid variable")
        self.name = string[0:-1]
    def __repr__(self):
        return f"{self.name}"
    __str__ = __repr__

def strToInfix(string):
    string = string.replace(" ", "")
    string = f"({string})"
    methods = [
           #(method, consumesLastCharacter)
            (getFloat, False),
            (variable, False),
            (operator, True)
            ]
    stack = []
    accum = ""
    count = -1
    while (count := count + 1) < len(string):
        char = string[count]
        accum += char
        for method, consumesLast in methods:
            try:
                stack.append(method(accum))
                accum = ""
                if not consumesLast:
                    count -= 1
            except ValueError:
                pass
    return stack

def isPrior(item, compare):
    priorityList = ("neg",), ("(", ")"), ("pow",), ("mul", "truediv"), ("add", "sub")
    for values in priorityList:
        if item in values:
            return compare not in values
        if compare in values:
                return False
    return False

def addOperator(stack, operatorStack, op):
    if len(operatorStack) == 0 or operatorStack[-1].name == "(" and op.name != ")":
        operatorStack.append(op)
        return
    if op.name == ")":
        while (nextOp := operatorStack.pop()).name != "(":
            stack.append(nextOp)
        return
    if isPrior(op.name, operatorStack[-1].name):
        operatorStack.append(op)
        return
    stack.append(operatorStack.pop())
    operatorStack.append(op)

def infixToPostfix(infix):
    stack = []
    operatorStack = []
    for index in range(len(infix)):
        item = infix[index]
        if isinstance(item, variable):
            if (
            len(stack) > 0 and isinstance(stack[-1], (float, int)) or
            isinstance(infix[index-1], operator) and infix[index-1].name == ")"
            ):
                addOperator(stack, operatorStack, operator("*"))
            stack.append(item)
        if isinstance(item, (float, int)):
            stack.append(item)
            continue
        if isinstance(item, operator):
            if (item.name == "sub" and (index == 0 or isinstance(infix[index - 1], operator))):
                item = operator("neg")
            addOperator(stack, operatorStack, item)
    stack.extend(operatorStack[::-1])
    return stack

def calculatePostfix(postfixList):
    stack = []
    for item in postfixList:
        if isinstance(item, variable):
            raise ValueError("Convert all variables to constant expressions")
        if isinstance(item, (int, float)):
            stack.append(float(item))
            continue
        if isinstance(item, operator):
            if item.binary:
                try:
                    op2 = stack.pop()
                    op1 = stack.pop()
                    stack.append(item(op1, op2))
                except IndexError:
                    raise ValueError("attempt to perform binary operation on stack of length <=1")
            else:
                try:
                    op = stack.pop()
                    stack.append(item(op))
                except IndexError:
                    raise ValueError("attempt to perform unary operation on stack of length 0")
    if len(stack) > 1:
        raise ValueError("unresolved expression")
    return stack[0]

@dataclass
class boundvariable:
    name: str
    occurrences: list
    position: int

def classifyVars(expression):
    variables = {}
    for index, item in enumerate(expression):
        if isinstance(item, variable):
            if item.name not in variables:
                newvar = boundvariable(item.name, [index], len(variables))
                variables.update({item.name: newvar})
            else:
                variables[item.name].occurrences.append(index)
    return variables

def getFunctionFromPostfix(expression):
    variables = classifyVars(expression)
    def f(*args):
        # args will be assigned variables in the expression in the order they appear.
        newExpression = expression[:]
        for v in variables.values():
            indices = v.occurrences
            position = v.position
            for i in indices:
                try:
                    newExpression[i] = args[position]
                except IndexError:
                    raise TypeError("Argument count mismatch.")
        return calculatePostfix(newExpression)
    return f

def getFunc(string):
    expression = strToInfix(string)
    postfix = infixToPostfix(expression)
    return getFunctionFromPostfix(postfix)

def calculateStr(string):
    expression = strToInfix(string)
    postfix = infixToPostfix(expression)
    return calculatePostfix(postfix)

def main():
    test_expressions = [
        "-5 - 1"
    ]

    for expr in test_expressions:
        try:
            result = getFunc(expr)
            print(f"f(3): {result(3, 2, 1, 3)}")
        except Exception as e:
            raise e
            print(f"Error evaluating '{expr}': {e}")

if __name__ == "__main__":
    main()
