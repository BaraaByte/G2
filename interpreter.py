from parser import ASTNode, NodeType
from typing import Dict, Any, List, Optional, Callable
import sys
import traceback
sys.dont_write_bytecode = True

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class BreakException(Exception):
    pass

class ContinueException(Exception):
    pass

class RaiseException(Exception):
    def __init__(self, value):
        self.value = value

class Environment:
    def __init__(self, parent=None):
        self.vars: Dict[str, Any] = {}
        self.parent = parent
        self.constants: Dict[str, bool] = {}  # Track if variable is constant
    
    def define(self, name: str, value: Any, is_const: bool = False):
        """Define a new variable"""
        self.vars[name] = value
        self.constants[name] = is_const
    
    def get(self, name: str) -> Any:
        """Get variable value"""
        if name in self.vars:
            return self.vars[name]
        elif self.parent:
            return self.parent.get(name)
        raise NameError(f"Variable '{name}' not defined")
    
    def set(self, name: str, value: Any):
        """Set variable value (mutable)"""
        if name in self.vars:
            if self.constants.get(name, False):
                raise TypeError(f"Cannot modify constant variable '{name}'")
            self.vars[name] = value
        elif self.parent:
            self.parent.set(name, value)
        else:
            raise NameError(f"Variable '{name}' not defined")

class Interpreter:
    def __init__(self, stdlib=None):
        self.global_env = Environment()
        self.current_env = self.global_env
        self.break_flag = False
        self.continue_flag = False
        
        # Load standard library
        if stdlib:
            for name, func in stdlib.items():
                if callable(func):
                    self.global_env.define(name, func, True)
                else:
                    self.global_env.define(name, func, True)
    
    def interpret(self, node: ASTNode) -> Any:
        """Interpret an AST node"""
        try:
            method = getattr(self, f"visit_{node.type.value.lower()}", self.generic_visit)
            return method(node)
        except ReturnException:
            raise
        except BreakException:
            raise
        except ContinueException:
            raise
        except RaiseException:
            raise
        except Exception as e:
            print(f"Runtime Error: {e}")
            traceback.print_exc()
            raise
    
    def generic_visit(self, node: ASTNode):
        """Fallback for unhandled node types"""
        raise Exception(f"No visitor for {node.type}")
    
    def visit_program(self, node: ASTNode):
        """Execute program"""
        result = None
        for child in node.children:
            result = self.interpret(child)
        return result
    
    def visit_entry(self, node: ASTNode):
        """Execute entry point"""
        return self.interpret(node.children[0])
    
    def visit_function(self, node: ASTNode):
        """Define a function"""
        name = node.value
        params_node = node.children[0]
        body_node = node.children[1]
        return_type = node.children[2].value if len(node.children) > 2 else None
        
        # Extract parameter names
        params = []
        for param_node in params_node.children:
            params.append(param_node.value)
        
        # Create closure
        def func(*args):
            # Create new environment
            old_env = self.current_env
            self.current_env = Environment(self.current_env)
            
            # Bind parameters
            for i, param in enumerate(params):
                if i < len(args):
                    self.current_env.define(param, args[i])
                else:
                    self.current_env.define(param, None)
            
            try:
                # Execute function body
                result = self.interpret(body_node)
                return result
            except ReturnException as ret:
                return ret.value
            finally:
                # Restore environment
                self.current_env = old_env
        
        self.current_env.define(name, func)
        return None
    
    def visit_let(self, node: ASTNode):
        """Handle variable declaration"""
        name = node.value
        value_node = node.children[0]
        mutable_node = node.children[1]
        type_node = node.children[2]
        
        value = self.interpret(value_node)
        is_const = not bool(mutable_node.value) if mutable_node else True
        
        # Type checking if type hint provided
        if type_node.value:
            # Simple type checking
            type_map = {
                'int': int,
                'float': float,
                'string': str,
                'bool': bool,
                'list': list
            }
            expected_type = type_map.get(type_node.value)
            if expected_type and not isinstance(value, expected_type):
                raise TypeError(f"Expected type {type_node.value}, got {type(value).__name__}")
        
        self.current_env.define(name, value, is_const)
        return value
    
    def visit_assign(self, node: ASTNode):
        """Handle assignment to mutable variable"""
        name = node.value
        value = self.interpret(node.children[0])
        
        self.current_env.set(name, value)
        return value
    
    def visit_var_ref(self, node: ASTNode):
        """Handle variable reference"""
        return self.current_env.get(node.value)
    
    def visit_if(self, node: ASTNode):
        """Handle if statement"""
        condition = self.interpret(node.children[0])
        then_block = node.children[1]
        elif_list = node.children[2] if len(node.children) > 2 else None
        else_block = node.children[3] if len(node.children) > 3 else None
        
        if self.is_truthy(condition):
            return self.interpret(then_block)
        elif elif_list:
            for elif_node in elif_list.children:
                elif_condition = self.interpret(elif_node.children[0])
                if self.is_truthy(elif_condition):
                    return self.interpret(elif_node.children[1])
        
        if else_block and else_block.value != NodeType.NONE:
            return self.interpret(else_block)
        
        return None
    
    def visit_for(self, node: ASTNode):
        """Handle for loop"""
        var_node = node.children[0]
        iterable_node = node.children[1]
        body_node = node.children[2]
        
        iterable = self.interpret(iterable_node)
        var_name = var_node.value
        
        try:
            # Handle range objects
            if isinstance(iterable, tuple) and len(iterable) == 2:
                # Range from a..b syntax
                start, end = iterable
                if isinstance(start, int) and isinstance(end, int):
                    for i in range(start, end + 1):
                        self.current_env.define(var_name, i, False)
                        self.interpret(body_node)
                        if self.break_flag:
                            self.break_flag = False
                            break
                        if self.continue_flag:
                            self.continue_flag = False
                            continue
            else:
                # Handle other iterables (lists, strings)
                for item in iterable:
                    self.current_env.define(var_name, item, False)
                    self.interpret(body_node)
                    if self.break_flag:
                        self.break_flag = False
                        break
                    if self.continue_flag:
                        self.continue_flag = False
                        continue
        except BreakException:
            pass
        except ContinueException:
            pass
        
        return None
    
    def visit_while(self, node: ASTNode):
        """Handle while loop"""
        condition_node = node.children[0]
        body_node = node.children[1]
        
        try:
            while self.is_truthy(self.interpret(condition_node)):
                self.interpret(body_node)
        except BreakException:
            pass
        except ContinueException:
            pass
        
        return None
    
    def visit_break(self, node: ASTNode):
        """Handle break statement"""
        raise BreakException()
    
    def visit_continue(self, node: ASTNode):
        """Handle continue statement"""
        raise ContinueException()
    
    def visit_return(self, node: ASTNode):
        """Handle return statement"""
        if node.children:
            value = self.interpret(node.children[0])
        else:
            value = None
        raise ReturnException(value)
    
    def visit_match(self, node: ASTNode):
        """Handle match expression"""
        value = self.interpret(node.children[0])
        cases_node = node.children[1]
        
        for case_node in cases_node.children:
            pattern_node, result_node = case_node.children
            
            if pattern_node.value == 'else':
                return self.interpret(result_node)
            
            pattern = self.interpret(pattern_node)
            
            # Check if pattern matches
            if self.match_pattern(value, pattern):
                return self.interpret(result_node)
        
        return None
    
    def match_pattern(self, value, pattern) -> bool:
        """Check if value matches pattern"""
        if isinstance(pattern, tuple) and len(pattern) == 2:
            # Range pattern
            start, end = pattern
            return start <= value <= end
        return value == pattern
    
    def visit_try(self, node: ASTNode):
        """Handle try-catch"""
        try_block = node.children[0]
        catch_node = node.children[1]
        err_var = catch_node.value
        catch_block = catch_node.children[0]
        
        try:
            return self.interpret(try_block)
        except RaiseException as e:
            # Store error in variable
            self.current_env.define(err_var, e.value, False)
            return self.interpret(catch_block)
        except Exception as e:
            self.current_env.define(err_var, str(e), False)
            return self.interpret(catch_block)
    
    def visit_raise(self, node: ASTNode):
        """Handle raise statement"""
        value = self.interpret(node.children[0])
        raise RaiseException(value)
    
    def visit_block(self, node: ASTNode):
        """Handle block of statements"""
        result = None
        for child in node.children:
            result = self.interpret(child)
        return result
    
    def visit_binary(self, node: ASTNode):
        """Handle binary operations"""
        left = self.interpret(node.children[0])
        right = self.interpret(node.children[1])
        op = node.value
        
        if op == '+':
            if isinstance(left, str) or isinstance(right, str):
                return str(left) + str(right)
            return left + right
        elif op == '-':
            return left - right
        elif op == '*':
            return left * right
        elif op == '/':
            return left / right
        elif op == '%':
            return left % right
        elif op == '**':
            return left ** right
        elif op == '==':
            return left == right
        elif op == '!=':
            return left != right
        elif op == '<':
            return left < right
        elif op == '>':
            return left > right
        elif op == '<=':
            return left <= right
        elif op == '>=':
            return left >= right
        elif op == '&&':
            return self.is_truthy(left) and self.is_truthy(right)
        elif op == '||':
            return self.is_truthy(left) or self.is_truthy(right)
        elif op == '??':
            return left if left is not None else right
        else:
            raise Exception(f"Unknown operator: {op}")
    
    def visit_unary(self, node: ASTNode):
        """Handle unary operations"""
        expr = self.interpret(node.children[0])
        op = node.value
        
        if op == '-':
            return -expr
        elif op == '+':
            return +expr
        elif op == '!':
            return not self.is_truthy(expr)
        else:
            raise Exception(f"Unknown unary operator: {op}")
    
    def visit_range(self, node: ASTNode):
        """Handle range expression (a..b)"""
        start = self.interpret(node.children[0])
        end = self.interpret(node.children[1])
        
        # Return as tuple for range iteration
        return (start, end)
    
    def visit_number(self, node: ASTNode):
        """Handle number literal"""
        return node.value
    
    def visit_string(self, node: ASTNode):
        """Handle string literal with interpolation"""
        value = node.value
        
        # Handle string interpolation {expr}
        if isinstance(value, str) and '{' in value:
            import re
            
            def replace_var(match):
                expr = match.group(1)
                # Parse and evaluate expression
                # For simplicity, just handle variable names
                return str(self.current_env.get(expr.strip()))
            
            # Simple interpolation for now
            # This could be enhanced to parse full expressions
            pattern = r'\{([^}]+)\}'
            return re.sub(pattern, replace_var, value)
        
        return value
    
    def visit_bool(self, node: ASTNode):
        """Handle boolean literal"""
        return node.value
    
    def visit_none(self, node: ASTNode):
        """Handle None literal"""
        return None
    
    def visit_list(self, node: ASTNode):
        """Handle list literal"""
        return [self.interpret(child) for child in node.children]
    
    def visit_index(self, node: ASTNode):
        """Handle index access"""
        collection = self.interpret(node.children[0])
        index = self.interpret(node.children[1])
        
        if isinstance(collection, (list, str, tuple)):
            return collection[index]
        else:
            raise TypeError(f"Cannot index {type(collection)}")
    
    def visit_call(self, node: ASTNode):
        """Handle function call"""
        func_name = node.value
        args = [self.interpret(arg) for arg in node.children]
        
        func = self.current_env.get(func_name)
        
        if callable(func):
            return func(*args)
        else:
            raise TypeError(f"'{func_name}' is not callable")
    
    def visit_expr(self, node: ASTNode):
        """Handle expression statement"""
        return self.interpret(node.children[0])
    
    def is_truthy(self, value) -> bool:
        """Check if value is truthy"""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        if isinstance(value, (list, tuple, dict)):
            return len(value) > 0
        return True