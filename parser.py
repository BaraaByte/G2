from lexer import TokenType, Token
from dataclasses import dataclass
import sys
from typing import List, Optional, Any

from enum import Enum
sys.dont_write_bytecode = True
class NodeType(Enum):
    # Program structure
    PROGRAM = 'PROGRAM'
    ENTRY = 'ENTRY'
    FUNCTION = 'FUNCTION'
    BLOCK = 'BLOCK'
    
    # Variables
    LET = 'LET'
    ASSIGN = 'ASSIGN'
    VAR_REF = 'VAR_REF'
    
    # Control flow
    IF = 'IF'
    FOR = 'FOR'
    WHILE = 'WHILE'
    RETURN = 'RETURN'
    BREAK = 'BREAK'
    CONTINUE = 'CONTINUE'
    MATCH = 'MATCH'
    CASE = 'CASE'
    
    # Expressions
    BINARY = 'BINARY'
    UNARY = 'UNARY'
    NUMBER = 'NUMBER'
    STRING = 'STRING'
    BOOL = 'BOOL'
    NONE = 'NONE'
    LIST = 'LIST'
    RANGE = 'RANGE'
    INDEX = 'INDEX'
    CALL = 'CALL'
    
    # Types
    TYPE = 'TYPE'
    IMPL = 'IMPL'
    STRUCT = 'STRUCT'
    
    # Error handling
    TRY = 'TRY'
    CATCH = 'CATCH'
    RAISE = 'RAISE'
    
    # Async
    ASYNC = 'ASYNC'
    AWAIT = 'AWAIT'

@dataclass
class ASTNode:
    type: NodeType
    value: Any = None
    children: List['ASTNode'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
    
    def __repr__(self):
        return f"{self.type}({self.value})"

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.current = tokens[0] if tokens else None
    
    def peek(self, offset: int = 0) -> Optional[Token]:
        """Look ahead without consuming"""
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else None
    
    def consume(self, *types: TokenType) -> Token:
        """Consume current token if it matches any type"""
        if not self.current:
            raise SyntaxError("Unexpected end of file")
        
        if self.current.type in types:
            token = self.current
            self.pos += 1
            self.current = self.tokens[self.pos] if self.pos < len(self.tokens) else None
            return token
        
        expected = ', '.join(t.value for t in types)
        raise SyntaxError(f"Expected {expected}, got {self.current.type.value} at line {self.current.line}")
    
    def match(self, *types: TokenType) -> bool:
        """Check if current token matches any type"""
        return self.current and self.current.type in types
    
    def parse(self) -> ASTNode:
        """Parse the entire program"""
        statements = []
        
        while self.current and self.current.type != TokenType.EOF:
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            
            # Skip newlines between statements
            while self.match(TokenType.NEWLINE):
                self.consume(TokenType.NEWLINE)
        
        return ASTNode(NodeType.PROGRAM, children=statements)
    
    def parse_statement(self) -> Optional[ASTNode]:
        """Parse a single statement"""
        if self.match(TokenType.ENTRY):
            return self.parse_entry()
        elif self.match(TokenType.FUNC):
            return self.parse_function()
        elif self.match(TokenType.LET):
            return self.parse_let()
        elif self.match(TokenType.IF):
            return self.parse_if()
        elif self.match(TokenType.FOR):
            return self.parse_for()
        elif self.match(TokenType.WHILE):
            return self.parse_while()
        elif self.match(TokenType.RETURN):
            return self.parse_return()
        elif self.match(TokenType.BREAK):
            self.consume(TokenType.BREAK)
            return ASTNode(NodeType.BREAK)
        elif self.match(TokenType.CONTINUE):
            self.consume(TokenType.CONTINUE)
            return ASTNode(NodeType.CONTINUE)
        elif self.match(TokenType.MATCH):
            return self.parse_match()
        elif self.match(TokenType.TYPE):
            return self.parse_type()
        elif self.match(TokenType.IMPL):
            return self.parse_impl()
        elif self.match(TokenType.TRY):
            return self.parse_try()
        elif self.match(TokenType.RAISE):
            return self.parse_raise()
        elif self.match(TokenType.ASYNC):
            return self.parse_async()
        else:
            expr = self.parse_expression()
            if expr:
                return ASTNode(NodeType.EXPR, children=[expr])
        return None
    
    def parse_entry(self) -> ASTNode:
        """Parse entry point: entry name block"""
        self.consume(TokenType.ENTRY)
        name = self.consume(TokenType.IDENT).value
        block = self.parse_block()
        return ASTNode(NodeType.ENTRY, name, [block])
    
    def parse_function(self) -> ASTNode:
        """Parse function: func name(params) [-> type] block"""
        self.consume(TokenType.FUNC)
        name = self.consume(TokenType.IDENT).value
        
        # Parameters
        self.consume(TokenType.LPAREN)
        params = []
        if not self.match(TokenType.RPAREN):
            while True:
                param = self.consume(TokenType.IDENT).value
                
                # Optional type annotation
                if self.match(TokenType.COLON):
                    self.consume(TokenType.COLON)
                    type_name = self.consume(TokenType.IDENT).value
                else:
                    type_name = None
                
                params.append((param, type_name))
                
                if self.match(TokenType.COMMA):
                    self.consume(TokenType.COMMA)
                else:
                    break
        self.consume(TokenType.RPAREN)
        
        # Optional return type
        return_type = None
        if self.match(TokenType.ARROW):
            self.consume(TokenType.ARROW)
            return_type = self.consume(TokenType.IDENT).value
        
        # Function body
        body = self.parse_block()
        
        return ASTNode(NodeType.FUNCTION, name, [
            ASTNode(NodeType.LIST, children=[ASTNode(NodeType.VAR_REF, p) for p, _ in params]),
            body,
            ASTNode(NodeType.STRING, return_type) if return_type else ASTNode(NodeType.NONE)
        ])
    
    def parse_let(self) -> ASTNode:
        """Parse variable declaration: let [mut] name := expr"""
        self.consume(TokenType.LET)
        
        # Check for mutability
        mutable = False
        if self.match(TokenType.MUT):
            self.consume(TokenType.MUT)
            mutable = True
        
        name = self.consume(TokenType.IDENT).value
        
        # Optional type annotation
        type_hint = None
        if self.match(TokenType.COLON):
            self.consume(TokenType.COLON)
            type_hint = self.consume(TokenType.IDENT).value
        
        self.consume(TokenType.ASSIGN)
        value = self.parse_expression()
        
        return ASTNode(NodeType.LET, name, [
            value,
            ASTNode(NodeType.BOOL, mutable),
            ASTNode(NodeType.STRING, type_hint) if type_hint else ASTNode(NodeType.NONE)
        ])
    
    def parse_if(self) -> ASTNode:
        """Parse if/elif/else chain"""
        self.consume(TokenType.IF)
        condition = self.parse_expression()
        then_block = self.parse_block()
        
        # Parse elif and else
        elif_blocks = []
        else_block = None
        
        while self.match(TokenType.ELIF):
            self.consume(TokenType.ELIF)
            elif_cond = self.parse_expression()
            elif_block = self.parse_block()
            elif_blocks.append((elif_cond, elif_block))
        
        if self.match(TokenType.ELSE):
            self.consume(TokenType.ELSE)
            else_block = self.parse_block()
        
        return ASTNode(NodeType.IF, None, [
            condition,
            then_block,
            ASTNode(NodeType.LIST, children=[
                ASTNode(NodeType.IF, children=[cond, block]) for cond, block in elif_blocks
            ]),
            else_block if else_block else ASTNode(NodeType.NONE)
        ])
    
    def parse_for(self) -> ASTNode:
        """Parse for loop: for var in range/iterable block"""
        self.consume(TokenType.FOR)
        var = self.consume(TokenType.IDENT).value
        self.consume(TokenType.IN)
        
        # Parse the iterable (could be range or list)
        iterable = self.parse_expression()
        
        # Loop body
        body = self.parse_block()
        
        return ASTNode(NodeType.FOR, None, [
            ASTNode(NodeType.VAR_REF, var),
            iterable,
            body
        ])
    
    def parse_while(self) -> ASTNode:
        """Parse while loop: while condition block"""
        self.consume(TokenType.WHILE)
        condition = self.parse_expression()
        body = self.parse_block()
        
        return ASTNode(NodeType.WHILE, None, [condition, body])
    
    def parse_return(self) -> ASTNode:
        """Parse return statement"""
        self.consume(TokenType.RETURN)
        
        if self.match(TokenType.NEWLINE, TokenType.DEDENT, TokenType.EOF, TokenType.RBRACE):
            return ASTNode(NodeType.RETURN, None)
        
        value = self.parse_expression()
        return ASTNode(NodeType.RETURN, None, [value])
    
    def parse_match(self) -> ASTNode:
        """Parse match expression"""
        self.consume(TokenType.MATCH)
        value = self.parse_expression()
        self.consume(TokenType.LBRACE)
        
        cases = []
        while not self.match(TokenType.RBRACE) and self.current:
            if self.match(TokenType.CASE):
                self.consume(TokenType.CASE)
                pattern = self.parse_expression()
                self.consume(TokenType.FAT_ARROW)
                result = self.parse_expression()
                cases.append((pattern, result))
            elif self.match(TokenType.ELSE):
                self.consume(TokenType.ELSE)
                self.consume(TokenType.FAT_ARROW)
                result = self.parse_expression()
                cases.append(('else', result))
        
        self.consume(TokenType.RBRACE)
        
        return ASTNode(NodeType.MATCH, None, [
            value,
            ASTNode(NodeType.LIST, children=[
                ASTNode(NodeType.CASE, children=[p, r]) for p, r in cases
            ])
        ])
    
    def parse_type(self) -> ASTNode:
        """Parse type definition"""
        self.consume(TokenType.TYPE)
        name = self.consume(TokenType.IDENT).value
        self.consume(TokenType.LBRACE)
        
        fields = []
        while not self.match(TokenType.RBRACE) and self.current:
            field_name = self.consume(TokenType.IDENT).value
            self.consume(TokenType.COLON)
            field_type = self.consume(TokenType.IDENT).value
            
            # Optional field
            optional = False
            if self.match(TokenType.QUEST):
                self.consume(TokenType.QUEST)
                optional = True
            
            fields.append((field_name, field_type, optional))
            
            if self.match(TokenType.COMMA):
                self.consume(TokenType.COMMA)
        
        self.consume(TokenType.RBRACE)
        
        return ASTNode(NodeType.TYPE, name, [
            ASTNode(NodeType.LIST, children=[
                ASTNode(NodeType.STRING, f) for f, _, _ in fields
            ])
        ])
    
    def parse_impl(self) -> ASTNode:
        """Parse implementation block"""
        self.consume(TokenType.IMPL)
        type_name = self.consume(TokenType.IDENT).value
        self.consume(TokenType.LBRACE)
        
        methods = []
        while not self.match(TokenType.RBRACE) and self.current:
            methods.append(self.parse_function())
        
        self.consume(TokenType.RBRACE)
        
        return ASTNode(NodeType.IMPL, type_name, methods)
    
    def parse_try(self) -> ASTNode:
        """Parse try-catch block"""
        self.consume(TokenType.TRY)
        try_block = self.parse_block()
        
        self.consume(TokenType.CATCH)
        err_var = self.consume(TokenType.IDENT).value
        catch_block = self.parse_block()
        
        return ASTNode(NodeType.TRY, None, [
            try_block,
            ASTNode(NodeType.CATCH, err_var, [catch_block])
        ])
    
    def parse_raise(self) -> ASTNode:
        """Parse raise statement"""
        self.consume(TokenType.RAISE)
        error = self.parse_expression()
        return ASTNode(NodeType.RAISE, None, [error])
    
    def parse_async(self) -> ASTNode:
        """Parse async function"""
        self.consume(TokenType.ASYNC)
        func = self.parse_function()
        return ASTNode(NodeType.ASYNC, None, [func])
    
    def parse_block(self) -> ASTNode:
        """Parse a block of statements"""
        statements = []
        
        if self.match(TokenType.INDENT):
            self.consume(TokenType.INDENT)
            
            while self.current and not self.match(TokenType.DEDENT):
                stmt = self.parse_statement()
                if stmt:
                    statements.append(stmt)
                
                while self.match(TokenType.NEWLINE):
                    self.consume(TokenType.NEWLINE)
            
            self.consume(TokenType.DEDENT)
        else:
            # Single statement block
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        
        return ASTNode(NodeType.BLOCK, children=statements)
    
    def parse_expression(self, precedence: int = 0) -> ASTNode:
        """Parse expression with precedence"""
        # Parse unary operators
        if self.match(TokenType.NOT, TokenType.MINUS, TokenType.PLUS):
            op = self.consume(TokenType.NOT, TokenType.MINUS, TokenType.PLUS)
            expr = self.parse_expression(8)  # Unary precedence
            return ASTNode(NodeType.UNARY, op.value, [expr])
        
        # Parse primary expression
        left = self.parse_primary()
        
        # Binary operators with precedence
        while True:
            if self.match(TokenType.OR) and 1 <= precedence:
                self.consume(TokenType.OR)
                right = self.parse_expression(1)
                left = ASTNode(NodeType.BINARY, '||', [left, right])
            
            elif self.match(TokenType.AND) and 2 <= precedence:
                self.consume(TokenType.AND)
                right = self.parse_expression(2)
                left = ASTNode(NodeType.BINARY, '&&', [left, right])
            
            elif self.match(TokenType.EQ, TokenType.NEQ) and 3 <= precedence:
                op = self.consume(TokenType.EQ, TokenType.NEQ)
                right = self.parse_expression(3)
                left = ASTNode(NodeType.BINARY, op.value, [left, right])
            
            elif self.match(TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE) and 4 <= precedence:
                op = self.consume(TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE)
                right = self.parse_expression(4)
                left = ASTNode(NodeType.BINARY, op.value, [left, right])
            
            elif self.match(TokenType.PLUS, TokenType.MINUS) and 5 <= precedence:
                op = self.consume(TokenType.PLUS, TokenType.MINUS)
                right = self.parse_expression(5)
                left = ASTNode(NodeType.BINARY, op.value, [left, right])
            
            elif self.match(TokenType.MUL, TokenType.DIV, TokenType.MOD) and 6 <= precedence:
                op = self.consume(TokenType.MUL, TokenType.DIV, TokenType.MOD)
                right = self.parse_expression(6)
                left = ASTNode(NodeType.BINARY, op.value, [left, right])
            
            elif self.match(TokenType.POW) and 7 <= precedence:
                self.consume(TokenType.POW)
                right = self.parse_expression(7)
                left = ASTNode(NodeType.BINARY, '**', [left, right])
            
            elif self.match(TokenType.RANGE) and 8 <= precedence:
                self.consume(TokenType.RANGE)
                right = self.parse_expression(8)
                left = ASTNode(NodeType.RANGE, None, [left, right])
            
            elif self.match(TokenType.NULL_COAL) and 9 <= precedence:
                self.consume(TokenType.NULL_COAL)
                right = self.parse_expression(9)
                left = ASTNode(NodeType.BINARY, '??', [left, right])
            
            else:
                break
        
        return left
    
    def parse_primary(self) -> ASTNode:
        """Parse primary expressions"""
        # Literals
        if self.match(TokenType.NUMBER):
            token = self.consume(TokenType.NUMBER)
            return ASTNode(NodeType.NUMBER, token.value)
        
        if self.match(TokenType.STRING):
            token = self.consume(TokenType.STRING)
            return ASTNode(NodeType.STRING, token.value)
        
        if self.match(TokenType.BOOL):
            token = self.consume(TokenType.BOOL)
            return ASTNode(NodeType.BOOL, token.value)
        
        if self.match(TokenType.NONE):
            self.consume(TokenType.NONE)
            return ASTNode(NodeType.NONE)
        
        # Grouping
        if self.match(TokenType.LPAREN):
            self.consume(TokenType.LPAREN)
            expr = self.parse_expression()
            self.consume(TokenType.RPAREN)
            return expr
        
        # Lists
        if self.match(TokenType.LBRACK):
            return self.parse_list()
        
        # Identifiers (variables, calls, indices)
        if self.match(TokenType.IDENT):
            name = self.consume(TokenType.IDENT).value
            
            # Function call
            if self.match(TokenType.LPAREN):
                self.consume(TokenType.LPAREN)
                args = []
                
                if not self.match(TokenType.RPAREN):
                    while True:
                        args.append(self.parse_expression())
                        if self.match(TokenType.COMMA):
                            self.consume(TokenType.COMMA)
                        else:
                            break
                
                self.consume(TokenType.RPAREN)
                return ASTNode(NodeType.CALL, name, args)
            
            # Index access
            if self.match(TokenType.LBRACK):
                self.consume(TokenType.LBRACK)
                index = self.parse_expression()
                self.consume(TokenType.RBRACK)
                return ASTNode(NodeType.INDEX, None, [
                    ASTNode(NodeType.VAR_REF, name),
                    index
                ])
            
            # Simple variable reference
            return ASTNode(NodeType.VAR_REF, name)
        
        raise SyntaxError(f"Unexpected token: {self.current}")
    
    def parse_list(self) -> ASTNode:
        """Parse list literal"""
        self.consume(TokenType.LBRACK)
        elements = []
        
        if not self.match(TokenType.RBRACK):
            while True:
                elements.append(self.parse_expression())
                if self.match(TokenType.COMMA):
                    self.consume(TokenType.COMMA)
                else:
                    break
        
        self.consume(TokenType.RBRACK)
        return ASTNode(NodeType.LIST, children=elements)