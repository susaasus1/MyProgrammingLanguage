import sys

from isa import Opcode, write_code, Term

number_variables = {}

string_variables = {}

indirect_variables = {}

command2opcode = {
    "+": Opcode.ADD.value,
    "-": Opcode.SUB.value,
    "*": Opcode.MUL.value,
    "/": Opcode.DIV.value,
    "%": Opcode.MOD.value,
}

commands = {
    "write",
    "read",
    "while",
    "endWhile",
    "initial",
    "calculate",
    "calculateVars",
    "calculateVar1",
    "calculateVar2",
    "initialVar",
    "if",
    "else",
    "endIf",
    "+",
    "-",
    "*",
    "/",
    "%"
}


def check_number(number):
    try:
        float(number)
        return True
    except ValueError:
        return False


def translate_to_terms(text):
    terms = []
    indirect_count = 512
    numbers_map = []
    strings_map = []
    indirect_map = []
    counter = 0
    for line_num, line in enumerate(text):
        line = line.strip()
        var = line.split(" ", 1)
        if var[0] == "":
            continue

        if var[0] == "number":
            if check_number(var[1][var[1].find('=') + 1:]):
                variable = var[1][:var[1].find('=')].strip()
                assert not (variable in number_variables), f"{variable} already initialized"
                number_variables[variable] = len(numbers_map)
                numbers_map.append(var[1][var[1].find('=') + 1:].strip())
                counter += 1

        if var[0] == "string":
            variable = var[1][:var[1].find('=')].strip()
            assert not (variable in string_variables), f"{variable} already initialized"
            string_variables[variable] = len(strings_map) + 1024
            indirect_variables[variable] = indirect_count
            indirect_count += 1
            indirect_map.append(len(strings_map) + 1024)
            for cr in var[1][var[1].find('"') + 1:].strip():
                if cr == '"':
                    break
                strings_map.append(ord(cr))
            strings_map.append(ord('\0'))
            counter += 1

        if var[0] in number_variables:
            operation = ""
            for elem in command2opcode:
                if var[1].find(elem) > -1:
                    operation = elem
                    operand1 = var[1][var[1].find('=') + 1:var[1].find(operation)].strip()
                    operand2 = var[1][var[1].find(operation) + 1:].strip()
                    if check_number(operand1) and check_number(operand2):
                        terms.append(Term(line_num - counter, "calculate", [var[0], operand1, operand2, operation]))
                    elif operand1 in number_variables and operand2 in number_variables:
                        terms.append(Term(line_num - counter, "calculateVars", [var[0], operand1, operand2, operation]))
                    elif operand1 in number_variables and check_number(operand2):
                        terms.append(Term(line_num - counter, "calculateVar1", [var[0], operand1, operand2, operation]))
                    elif operand2 in number_variables and check_number(operand1):
                        terms.append(Term(line_num - counter, "calculateVar2", [var[0], operand1, operand2, operation]))

            if operation == "":
                operand1 = var[1][var[1].find('=') + 1:].strip()
                if check_number(operand1):
                    terms.append(Term(line_num - counter, "initial", [var[0], operand1]))
                elif operand1 in number_variables:
                    terms.append(Term(line_num - counter, "initialVar", [var[0], operand1]))

        if var[0] in commands or var[0][:var[0].find('(')] in commands:
            if var[0].find('(') > -1 and var[0].find(')') > -1:

                if var[0][:var[0].find('(')].strip() == "write":

                    if var[0][var[0].find('(') + 1:var[0].find(')')] in string_variables:
                        terms.append(
                            Term(line_num - counter, "writes",
                                 indirect_variables[var[0][var[0].find('(') + 1:var[0].find(')')]]))
                    if var[0][var[0].find('(') + 1:var[0].find(')')] in number_variables:
                        terms.append(
                            Term(line_num - counter, "writen",
                                 number_variables[var[0][var[0].find('(') + 1:var[0].find(')')]]))

                elif var[0][:var[0].find('(')].strip() == "read":
                    if var[0][var[0].find('(') + 1:var[0].find(')')] in string_variables:
                        terms.append(
                            Term(line_num - counter, "reads",
                                 indirect_variables[var[0][var[0].find('(') + 1:var[0].find(')')]]))
                    if var[0][var[0].find('(') + 1:var[0].find(')')] in number_variables:
                        terms.append(
                            Term(line_num - counter, "readn",
                                 number_variables[var[0][var[0].find('(') + 1:var[0].find(')')]]))

                elif var[0][:var[0].find('(')].strip() == "while":
                    assert var[0][var[0].find('(') + 1:var[0].find(')')] in number_variables, "Syntax error"
                    terms.append(Term(line_num - counter, "while",
                                      number_variables[var[0][var[0].find('(') + 1:var[0].find(')')]]))

                else:
                    terms.append(
                        Term(line_num - counter, var[0][:var[0].find('(')].strip(),
                             var[0][var[0].find('(') + 1:var[0].find(')')]))

            assert var[0].find('(') or var[0].find(')'), "Syntax error!"
            if var[0].find('(') == -1 and var[0].find(')') == -1:
                terms.append(Term(line_num - counter, var[0], None))

    return numbers_map, strings_map, indirect_map, terms


def translate_to_opcode(text):
    numbers_map, strings_map, indirect_map, terms = translate_to_terms(text)
    check_brackets(terms)

    code = []
    jmp_stack = []
    terms_stack = []
    for i, term in enumerate(terms):
        if term.var == "calculate" and term.arg is not None:
            code.append({"opcode": Opcode.MOV.value, "arg": term.arg[1]})
            if term.arg[3] in command2opcode:
                code.append({"opcode": command2opcode[term.arg[3]], "arg": "$" + term.arg[2]})
            if term.arg[0] in number_variables:
                code.append({"opcode": Opcode.WR_MEM.value, "arg": number_variables[term.arg[0]]})
        elif term.var == "calculateVars":
            code.append({"opcode": Opcode.RD_MEM.value, "arg": number_variables[term.arg[1]]})
            if term.arg[3] in command2opcode:
                code.append({"opcode": command2opcode[term.arg[3]], "arg": number_variables[term.arg[2]]})
            if term.arg[0] in number_variables:
                code.append({"opcode": Opcode.WR_MEM.value, "arg": number_variables[term.arg[0]]})
        elif term.var == "calculateVar1":
            code.append({"opcode": Opcode.RD_MEM.value, "arg": number_variables[term.arg[1]]})
            if term.arg[3] in command2opcode:
                code.append({"opcode": command2opcode[term.arg[3]], "arg": "$" + term.arg[2]})
            if term.arg[0] in number_variables:
                code.append({"opcode": Opcode.WR_MEM.value, "arg": number_variables[term.arg[0]]})
        elif term.var == "calculateVar2":
            code.append({"opcode": Opcode.MOV.value, "arg": term.arg[1]})
            if term.arg[3] in command2opcode:
                code.append({"opcode": command2opcode[term.arg[3]], "arg": number_variables[term.arg[2]]})
            if term.arg[0] in number_variables:
                code.append({"opcode": Opcode.WR_MEM.value, "arg": number_variables[term.arg[0]]})

        elif term.var == "initial":
            code.append({"opcode": Opcode.MOV.value, "arg": term.arg[1]})
            code.append({"opcode": Opcode.WR_MEM.value, "arg": number_variables[term.arg[0]]})
        elif term.var == "initialVar":
            code.append({"opcode": Opcode.RD_MEM.value, "arg": number_variables[term.arg[1]]})
            code.append({"opcode": Opcode.WR_MEM.value, "arg": number_variables[term.arg[0]]})

        elif term.var == "if":
            code.append(None)
            code.append(None)
            code.append(None)
            terms_stack.append(i)
            jmp_stack.append(len(code) - 1)
            jmp_stack.append(len(code) - 2)
            jmp_stack.append(len(code) - 3)
        elif term.var == "else":
            code.append(None)
            jmp_stack.append(len(code) - 1)
        elif term.var == "endIf":
            jmp_to_load = {}
            jmp_to_sub = {}
            else_ind = jmp_stack.pop()
            load = jmp_stack.pop()
            sub = jmp_stack.pop()
            if_ind = jmp_stack.pop()
            term_if_ind = terms_stack.pop()
            operand1 = terms[term_if_ind].arg[:terms[term_if_ind].arg.find('=')]
            operand2 = terms[term_if_ind].arg[terms[term_if_ind].arg.find('=') + 2:]
            assert operand1 in number_variables or operand2 in number_variables, "Syntax Error: Two numbers in " \
                                                                                 "command IF"
            if operand1 in number_variables and check_number(operand2):
                jmp_to_load = {"opcode": Opcode.RD_MEM.value, "arg": number_variables[operand1]}
                jmp_to_sub = {"opcode": Opcode.SUB.value, "arg": '$' + operand2}
            elif operand2 in number_variables and check_number(operand1):
                jmp_to_load = {"opcode": Opcode.MOV.value, "arg": operand2}
                jmp_to_sub = {"opcode": Opcode.SUB.value, "arg": number_variables[operand1]}
            elif operand1 in number_variables and operand2 in number_variables:
                jmp_to_load = {"opcode": Opcode.RD_MEM.value, "arg": number_variables[operand1]}
                jmp_to_sub = {"opcode": Opcode.SUB.value, "arg": number_variables[operand2]}
            jmp_else = {"opcode": Opcode.JNZ.value, "arg": else_ind + 1}
            jmp_then = {"opcode": Opcode.JMP.value, "arg": len(code)}
            code[load] = jmp_to_load
            code[sub] = jmp_to_sub
            code[if_ind] = jmp_else
            code[else_ind] = jmp_then
            code.append({"opcode": Opcode.NOP.value})

        elif term.var == "while":
            code.append(None)
            code.append(None)
            terms_stack.append(i)
            jmp_stack.append(len(code) - 1)
            jmp_stack.append(len(code) - 2)
        elif term.var == "endWhile":
            load = jmp_stack.pop()
            wh = jmp_stack.pop()
            wh_term = terms_stack.pop()
            jmp_to_load = {'opcode': Opcode.RD_MEM.value, "arg": terms[wh_term].arg}
            jmp_to_end = {'opcode': Opcode.JZ.value, "arg": len(code) + 1}
            jmp_to_while = {'opcode': Opcode.JMP.value, "arg": load}
            code[load] = jmp_to_load
            code[wh] = jmp_to_end
            code.append(jmp_to_while)

        elif term.var == "writes":
            code.append({'opcode': Opcode.WR_NMEM.value, "arg": term.arg})
        elif term.var == "writen":
            code.append({'opcode': Opcode.WR_BUF.value, "arg": term.arg})

        elif term.var == "reads":
            code.append({'opcode': Opcode.RD_NMEM.value, "arg": term.arg})
        elif term.var == "readn":
            code.append({'opcode': Opcode.RD_BUF.value, "arg": term.arg})

        elif term.arg is None:
            code.append({'opcode': command2opcode[term.var]})
        else:
            code.append({'opcode': command2opcode[term.var], "arg": term.arg})

    code.append({'opcode': Opcode.HLT.value})

    return strings_map, numbers_map, indirect_map, code, len(text)


def check_brackets(terms):
    deep_if = 0
    deep_else = 0
    for term in terms:
        if term.var == "if":
            deep_if += 1
        if term.var == "else":
            deep_if -= 1
            deep_else += 1
        if term.var == "endIf":
            assert deep_if + 1 == deep_else, "Unbalanced brackets!"
            deep_else -= 1
        assert deep_if >= 0 and deep_else >= 0, "Unbalanced brackets!"
    assert deep_if == 0 and deep_else == 0, "Unbalanced brackets!"

    deep = 0
    for term in terms:
        if term.var == "while":
            deep += 1
        if term.var == "endWhile":
            deep -= 1
        assert deep >= 0, "Unbalanced brackets!"
    assert deep == 0, "Unbalanced brackets!"


def main(args):
    assert len(args) == 3, "Wrong arguments: translator.py <input_file> <target_file> <data_section_file>"
    source, target, data = args
    with open(source, "rt", encoding="utf-8") as f:
        source = f.readlines()

    strings, numbers, indirect, code, loc = translate_to_opcode(source)
    print("source LoC:", len(source), "code instr:", len(code))
    number_variables.clear()
    string_variables.clear()
    indirect_variables.clear()
    write_code(target, code, strings, numbers, indirect, data)


if __name__ == "__main__":
    main(sys.argv[1:])
