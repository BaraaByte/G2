import re
import hashlib
import pickle
import os
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path
import sys
sys.dont_write_bytecode = True

class TokenType(Enum):
    # Keywords
    ENTRY = 'ENTRY'
    FUNC = 'FUNC'
    LET = 'LET'
    MUT = 'MUT'
    IF = 'IF'
    ELIF = 'ELIF'
    ELSE = 'ELSE'
    FOR = 'FOR'
    IN = 'IN'
    WHILE = 'WHILE'
    RETURN = 'RETURN'
    BREAK = 'BREAK'
    CONTINUE = 'CONTINUE'
    MATCH = 'MATCH'
    CASE = 'CASE'
    TYPE = 'TYPE'
    IMPL = 'IMPL'
    ASYNC = 'ASYNC'
    AWAIT = 'AWAIT'
    TRY = 'TRY'
    CATCH = 'CATCH'
    RAISE = 'RAISE'
    
    # Literals
    NUMBER = 'NUMBER'
    STRING = 'STRING'
    BOOL = 'BOOL'
    NONE = 'NONE'
    IDENT = 'IDENT'
    
    # Operators
    ASSIGN = 'ASSIGN'           # :=
    EQ = 'EQ'                   # ==
    NEQ = 'NEQ'                 # !=
    LT = 'LT'                   # <
    GT = 'GT'                   # >
    LTE = 'LTE'                 # <=
    GTE = 'GTE'                 # >=
    PLUS = 'PLUS'               # +
    MINUS = 'MINUS'             # -
    MUL = 'MUL'                 # *
    DIV = 'DIV'                 # /
    MOD = 'MOD'                 # %
    POW = 'POW'                 # **
    AND = 'AND'                 # &&
    OR = 'OR'                   # ||
    NOT = 'NOT'                 # !
    ARROW = 'ARROW'             # ->
    FAT_ARROW = 'FAT_ARROW'     # =>
    RANGE = 'RANGE'             # ..
    NULL_COAL = 'NULL_COAL'     # ??
    
    # Delimiters
    LPAREN = 'LPAREN'           # (
    RPAREN = 'RPAREN'           # )
    LBRACE = 'LBRACE'           # {
    RBRACE = 'RBRACE'           # }
    LBRACK = 'LBRACK'           # [
    RBRACK = 'RBRACK'           # ]
    COMMA = 'COMMA'             # ,
    COLON = 'COLON'             # :
    SEMI = 'SEMI'               # ;
    DOT = 'DOT'                 # .
    QUEST = 'QUEST'             # ?
    AT = 'AT'                   # @
    
    # Special
    NEWLINE = 'NEWLINE'
    INDENT = 'INDENT'
    DEDENT = 'DEDENT'
    EOF = 'EOF'
    COMMENT = 'COMMENT'

@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    column: int
    file: str = ""
    
    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)}, {self.line}:{self.column})"

class LexerCache:
    """Cache system for lexer tokens"""
    def __init__(self, cache_dir: str = ".g2_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_file_hash(self, filepath: str, source: str) -> str:
        """Generate hash from file path and content"""
        content_hash = hashlib.sha256(source.encode()).hexdigest()
        path_hash = hashlib.sha256(filepath.encode()).hexdigest()
        return f"{path_hash}_{content_hash[:16]}"
    
    def _get_cache_path(self, file_hash: str) -> Path:
        """Get cache file path"""
        return self.cache_dir / f"lexer_{file_hash}.cache"
    
    def get_cached_tokens(self, filepath: str, source: str) -> Optional[List[Token]]:
        """Retrieve cached tokens if they exist"""
        file_hash = self._get_file_hash(filepath, source)
        cache_path = self._get_cache_path(file_hash)
        
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except:
                return None
        return None
    
    def cache_tokens(self, filepath: str, source: str, tokens: List[Token]) -> None:
        """Cache tokens for future use"""
        file_hash = self._get_file_hash(filepath, source)
        cache_path = self._get_cache_path(file_hash)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(tokens, f)
        except:
            pass  # Silently fail if caching fails

class Lexer:
    def __init__(self, source: str, filename: str = "<stdin>"):
        self.source = source
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []
        self.indent_stack = [0]
        
        # Keywords mapping
        self.keywords = {
            'entry': TokenType.ENTRY,
            'func': TokenType.FUNC,
            'let': TokenType.LET,
            'mut': TokenType.MUT,
            'if': TokenType.IF,
            'elif': TokenType.ELIF,
            'else': TokenType.ELSE,
            'for': TokenType.FOR,
            'in': TokenType.IN,
            'while': TokenType.WHILE,
            'return': TokenType.RETURN,
            'break': TokenType.BREAK,
            'continue': TokenType.CONTINUE,
            'match': TokenType.MATCH,
            'case': TokenType.CASE,
            'type': TokenType.TYPE,
            'impl': TokenType.IMPL,
            'async': TokenType.ASYNC,
            'await': TokenType.AWAIT,
            'try': TokenType.TRY,
            'catch': TokenType.CATCH,
            'raise': TokenType.RAISE,
            'true': TokenType.BOOL,
            'false': TokenType.BOOL,
            'none': TokenType.NONE,
        }
    
    def tokenize(self) -> List[Token]:
        """Convert source to tokens"""
        while self.pos < len(self.source):
            ch = self.source[self.pos]
            
            # Handle whitespace
            if ch in ' \t':
                self.pos += 1
                self.col += 1
                continue
            
            # Handle newlines with indentation
            if ch == '\n':
                self._handle_newline()
                continue
            
            # Handle comments
            if ch == '/' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == '/':
                self._skip_comment()
                continue
            
            # Handle numbers
            if ch.isdigit() or (ch == '.' and self.pos + 1 < len(self.source) and self.source[self.pos + 1].isdigit()):
                self._scan_number()
                continue
            
            # Handle strings
            if ch in '"\'':
                self._scan_string()
                continue
            
            # Handle identifiers and keywords
            if ch.isalpha() or ch == '_':
                self._scan_identifier()
                continue
            
            # Handle operators and delimiters
            self._scan_operator()
        
        # Close remaining indents
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token(TokenType.DEDENT, None, self.line, self.col, self.filename))
        
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.col, self.filename))
        return self.tokens
    
    def _handle_newline(self):
        """Handle newline with indentation tracking"""
        self.tokens.append(Token(TokenType.NEWLINE, '\n', self.line, self.col, self.filename))
        self.line += 1
        self.col = 1
        self.pos += 1
        
        # Calculate indentation
        indent = 0
        while self.pos < len(self.source) and self.source[self.pos] in ' \t':
            if self.source[self.pos] == ' ':
                indent += 1
            elif self.source[self.pos] == '\t':
                indent += 4
            self.pos += 1
            self.col += 1
        
        if indent > self.indent_stack[-1]:
            self.indent_stack.append(indent)
            self.tokens.append(Token(TokenType.INDENT, indent, self.line, self.col, self.filename))
        elif indent < self.indent_stack[-1]:
            while indent < self.indent_stack[-1]:
                self.indent_stack.pop()
                self.tokens.append(Token(TokenType.DEDENT, None, self.line, self.col, self.filename))
    
    def _skip_comment(self):
        """Skip single-line comments"""
        start_line = self.line
        start_col = self.col
        while self.pos < len(self.source) and self.source[self.pos] != '\n':
            self.pos += 1
            self.col += 1
        
        comment = self.source[start_col-1:self.pos]
        self.tokens.append(Token(TokenType.COMMENT, comment.strip(), start_line, start_col, self.filename))
    
    def _scan_number(self):
        """Scan numeric literals"""
        start = self.pos
        start_line = self.line
        start_col = self.col
        is_float = False
        
        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch.isdigit():
                self.pos += 1
                self.col += 1
            elif ch == '.' and not is_float:
                is_float = True
                self.pos += 1
                self.col += 1
            else:
                break
        
        num_str = self.source[start:self.pos]
        if is_float:
            value = float(num_str)
        else:
            value = int(num_str)
        
        self.tokens.append(Token(TokenType.NUMBER, value, start_line, start_col, self.filename))
    
    def _scan_string(self):
        """Scan string literals"""
        quote = self.source[self.pos]
        start_line = self.line
        start_col = self.col
        self.pos += 1
        self.col += 1
        
        value = []
        escaped = False
        
        while self.pos < len(self.source):
            ch = self.source[self.pos]
            
            if escaped:
                if ch == 'n':
                    value.append('\n')
                elif ch == 't':
                    value.append('\t')
                elif ch == 'r':
                    value.append('\r')
                elif ch == '"':
                    value.append('"')
                elif ch == "'":
                    value.append("'")
                elif ch == '\\':
                    value.append('\\')
                elif ch == '{':
                    value.append('{')  # For interpolation
                else:
                    value.append('\\' + ch)
                escaped = False
                self.pos += 1
                self.col += 1
                continue
            
            if ch == '\\':
                escaped = True
                self.pos += 1
                self.col += 1
                continue
            
            if ch == quote:
                self.pos += 1
                self.col += 1
                break
            
            value.append(ch)
            self.pos += 1
            self.col += 1
        
        self.tokens.append(Token(TokenType.STRING, ''.join(value), start_line, start_col, self.filename))
    
    def _scan_identifier(self):
        """Scan identifiers and keywords"""
        start = self.pos
        start_line = self.line
        start_col = self.col
        
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            self.pos += 1
            self.col += 1
        
        ident = self.source[start:self.pos]
        token_type = self.keywords.get(ident, TokenType.IDENT)
        
        if ident == 'true':
            value = True
        elif ident == 'false':
            value = False
        elif ident == 'none':
            value = None
        else:
            value = ident
        
        self.tokens.append(Token(token_type, value, start_line, start_col, self.filename))
    
    def _scan_operator(self):
        """Scan operators and delimiters"""
        ch = self.source[self.pos]
        start_line = self.line
        start_col = self.col
        
        # Multi-character operators
        if ch == ':' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == '=':
            self.tokens.append(Token(TokenType.ASSIGN, ':=', start_line, start_col, self.filename))
            self.pos += 2
            self.col += 2
        elif ch == '=' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == '=':
            self.tokens.append(Token(TokenType.EQ, '==', start_line, start_col, self.filename))
            self.pos += 2
            self.col += 2
        elif ch == '!' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == '=':
            self.tokens.append(Token(TokenType.NEQ, '!=', start_line, start_col, self.filename))
            self.pos += 2
            self.col += 2
        elif ch == '<' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == '=':
            self.tokens.append(Token(TokenType.LTE, '<=', start_line, start_col, self.filename))
            self.pos += 2
            self.col += 2
        elif ch == '>' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == '=':
            self.tokens.append(Token(TokenType.GTE, '>=', start_line, start_col, self.filename))
            self.pos += 2
            self.col += 2
        elif ch == '&' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == '&':
            self.tokens.append(Token(TokenType.AND, '&&', start_line, start_col, self.filename))
            self.pos += 2
            self.col += 2
        elif ch == '|' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == '|':
            self.tokens.append(Token(TokenType.OR, '||', start_line, start_col, self.filename))
            self.pos += 2
            self.col += 2
        elif ch == '-' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == '>':
            self.tokens.append(Token(TokenType.ARROW, '->', start_line, start_col, self.filename))
            self.pos += 2
            self.col += 2
        elif ch == '=' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == '>':
            self.tokens.append(Token(TokenType.FAT_ARROW, '=>', start_line, start_col, self.filename))
            self.pos += 2
            self.col += 2
        elif ch == '.' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == '.':
            self.tokens.append(Token(TokenType.RANGE, '..', start_line, start_col, self.filename))
            self.pos += 2
            self.col += 2
        elif ch == '?' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == '?':
            self.tokens.append(Token(TokenType.NULL_COAL, '??', start_line, start_col, self.filename))
            self.pos += 2
            self.col += 2
        elif ch == '*' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == '*':
            self.tokens.append(Token(TokenType.POW, '**', start_line, start_col, self.filename))
            self.pos += 2
            self.col += 2
        
        # Single-character operators
        elif ch == '+':
            self.tokens.append(Token(TokenType.PLUS, '+', start_line, start_col, self.filename))
            self.pos += 1
            self.col += 1
        elif ch == '-':
            self.tokens.append(Token(TokenType.MINUS, '-', start_line, start_col, self.filename))
            self.pos += 1
            self.col += 1
        elif ch == '*':
            self.tokens.append(Token(TokenType.MUL, '*', start_line, start_col, self.filename))
            self.pos += 1
            self.col += 1
        elif ch == '/':
            self.tokens.append(Token(TokenType.DIV, '/', start_line, start_col, self.filename))
            self.pos += 1
            self.col += 1
        elif ch == '%':
            self.tokens.append(Token(TokenType.MOD, '%', start_line, start_col, self.filename))
            self.pos += 1
            self.col += 1
        elif ch == '!':
            self.tokens.append(Token(TokenType.NOT, '!', start_line, start_col, self.filename))
            self.pos += 1
            self.col += 1
        elif ch == '=':
            self.tokens.append(Token(TokenType.ASSIGN, '=', start_line, start_col, self.filename))  # Simple assignment fallback
            self.pos += 1
            self.col += 1
        elif ch == '<':
            self.tokens.append(Token(TokenType.LT, '<', start_line, start_col, self.filename))
            self.pos += 1
            self.col += 1
        elif ch == '>':
            self.tokens.append(Token(TokenType.GT, '>', start_line, start_col, self.filename))
            self.pos += 1
            self.col += 1
        
        # Delimiters
        elif ch == '(':
            self.tokens.append(Token(TokenType.LPAREN, '(', start_line, start_col, self.filename))
            self.pos += 1
            self.col += 1
        elif ch == ')':
            self.tokens.append(Token(TokenType.RPAREN, ')', start_line, start_col, self.filename))
            self.pos += 1
            self.col += 1
        elif ch == '{':
            self.tokens.append(Token(TokenType.LBRACE, '{', start_line, start_col, self.filename))
            self.pos += 1
            self.col += 1
        elif ch == '}':
            self.tokens.append(Token(TokenType.RBRACE, '}', start_line, start_col, self.filename))
            self.pos += 1
            self.col += 1
        elif ch == '[':
            self.tokens.append(Token(TokenType.LBRACK, '[', start_line, start_col, self.filename))
            self.pos += 1
            self.col += 1
        elif ch == ']':
            self.tokens.append(Token(TokenType.RBRACK, ']', start_line, start_col, self.filename))
            self.pos += 1
            self.col += 1
        elif ch == ',':
            self.tokens.append(Token(TokenType.COMMA, ',', start_line, start_col, self.filename))
            self.pos += 1
            self.col += 1
        elif ch == ':':
            self.tokens.append(Token(TokenType.COLON, ':', start_line, start_col, self.filename))
            self.pos += 1
            self.col += 1
        elif ch == ';':
            self.tokens.append(Token(TokenType.SEMI, ';', start_line, start_col, self.filename))
            self.pos += 1
            self.col += 1
        elif ch == '.':
            self.tokens.append(Token(TokenType.DOT, '.', start_line, start_col, self.filename))
            self.pos += 1
            self.col += 1
        elif ch == '?':
            self.tokens.append(Token(TokenType.QUEST, '?', start_line, start_col, self.filename))
            self.pos += 1
            self.col += 1
        elif ch == '@':
            self.tokens.append(Token(TokenType.AT, '@', start_line, start_col, self.filename))
            self.pos += 1
            self.col += 1
        
        else:
            # Skip unknown characters
            self.pos += 1
            self.col += 1