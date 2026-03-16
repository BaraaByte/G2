#!/usr/bin/env python3

import sys
import os
import argparse
import time
from pathlib import Path
from lexer import Lexer, LexerCache
from parser import Parser
from interpreter import Interpreter
from stdlib import get_stdlib
sys.dont_write_bytecode = True
class G2CLI:
    def __init__(self):
        self.stdlib = get_stdlib()
        self.interpreter = Interpreter(self.stdlib)
        self.lexer_cache = LexerCache()
        self.debug = False
    
    def run_file(self, filename, use_cache=True):
        """Run a G2 file with caching"""
        try:
            with open(filename, 'r') as f:
                source = f.read()
            
            start_time = time.time()
            
            # Lexical analysis with caching
            if use_cache:
                tokens = self.lexer_cache.get_cached_tokens(filename, source)
                if tokens:
                    if self.debug:
                        print(f"[Cache] Loaded tokens for {filename}")
                else:
                    lexer = Lexer(source, filename)
                    tokens = lexer.tokenize()
                    self.lexer_cache.cache_tokens(filename, source, tokens)
                    if self.debug:
                        print(f"[Cache] Generated tokens for {filename}")
            else:
                lexer = Lexer(source, filename)
                tokens = lexer.tokenize()
            
            if self.debug:
                print(f"[Lexer] {len(tokens)} tokens generated")
                for token in tokens[:20]:  # Show first 20 tokens
                    print(f"  {token}")
            
            # Parsing
            parser = Parser(tokens)
            ast = parser.parse()
            
            if self.debug:
                print(f"[Parser] AST generated")
                self.print_ast(ast)
            
            # Interpretation
            result = self.interpreter.interpret(ast)
            
            elapsed = time.time() - start_time
            if self.debug:
                print(f"[Time] {elapsed:.3f}s")
            
            return result
            
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found")
            sys.exit(1)
        except SyntaxError as e:
            print(f"Syntax Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Runtime Error: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    def run_source(self, source, filename='<stdin>'):
        """Run G2 source code"""
        try:
            lexer = Lexer(source, filename)
            tokens = lexer.tokenize()
            
            parser = Parser(tokens)
            ast = parser.parse()
            
            result = self.interpreter.interpret(ast)
            
            return result
        except Exception as e:
            print(f"Error: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    def run_repl(self):
        """Run interactive REPL"""
        print("\033[1;32m")  # Green
        print("╔════════════════════════════════╗")
        print("║     G2 Programming Language    ║")
        print("║         Version 2.0            ║")
        print("╚════════════════════════════════╝")
        print("\033[0m")  # Reset
        print("Type 'exit()' to quit")
        print()
        
        while True:
            try:
                # Multi-line input
                lines = []
                while True:
                    if not lines:
                        line = input('\033[1;36mg2>\033[0m ')
                    else:
                        line = input('... ')
                    
                    if not line.strip():
                        break
                    
                    lines.append(line)
                    
                    # Check if we have a complete statement
                    if line.rstrip().endswith('}') or line.rstrip().endswith(';'):
                        break
                
                source = '\n'.join(lines)
                
                if source.strip() == 'exit()':
                    break
                
                if source.strip():
                    # Run the code
                    result = self.run_source(source)
                    
                    # Print result if not None
                    if result is not None:
                        print(f"\033[1;33m=> {result}\033[0m")
            
            except KeyboardInterrupt:
                print("\nUse 'exit()' to quit")
            except EOFError:
                break
    
    def compile_file(self, filename, output=None):
        """Compile G2 file to bytecode"""
        print("Compiling to bytecode...")
        
        try:
            with open(filename, 'r') as f:
                source = f.read()
            
            # Generate bytecode (simplified - just save AST for now)
            lexer = Lexer(source, filename)
            tokens = lexer.tokenize()
            
            parser = Parser(tokens)
            ast = parser.parse()
            
            # Save compiled bytecode
            if not output:
                output = filename.replace('.g2', '.g2c')
            
            import pickle
            with open(output, 'wb') as f:
                pickle.dump({
                    'ast': ast,
                    'source': source,
                    'filename': filename
                }, f)
            
            print(f"Compiled to {output}")
            
        except Exception as e:
            print(f"Compilation error: {e}")
            sys.exit(1)
    
    def run_bytecode(self, filename):
        """Run compiled bytecode"""
        try:
            import pickle
            with open(filename, 'rb') as f:
                data = pickle.load(f)
            
            ast = data['ast']
            result = self.interpreter.interpret(ast)
            
            return result
        except Exception as e:
            print(f"Error running bytecode: {e}")
            sys.exit(1)
    
    def show_ast(self, filename):
        """Show AST for a file"""
        try:
            with open(filename, 'r') as f:
                source = f.read()
            
            lexer = Lexer(source, filename)
            tokens = lexer.tokenize()
            
            parser = Parser(tokens)
            ast = parser.parse()
            
            self.print_ast(ast)
        except Exception as e:
            print(f"Error: {e}")
    
    def print_ast(self, node, level=0):
        """Pretty print AST with colors"""
        indent = '  ' * level
        color = '\033[1;34m' if level == 0 else '\033[0m'
        
        print(f"{indent}{color}{node.type}", end='')
        
        if node.value is not None:
            print(f": \033[1;33m{node.value}\033[0m")
        else:
            print('\033[0m')
        
        for child in node.children:
            self.print_ast(child, level + 1)
    
    def show_tokens(self, filename):
        """Show tokens for a file"""
        try:
            with open(filename, 'r') as f:
                source = f.read()
            
            lexer = Lexer(source, filename)
            tokens = lexer.tokenize()
            
            for token in tokens:
                if token.type.name == 'COMMENT':
                    print(f"\033[2;37m{token}\033[0m")
                else:
                    print(token)
        except Exception as e:
            print(f"Error: {e}")
    
    def clear_cache(self):
        """Clear the lexer cache"""
        cache_dir = Path(".g2_cache")
        if cache_dir.exists():
            import shutil
            shutil.rmtree(cache_dir)
            print("Cache cleared")
        else:
            print("No cache found")

def main():
    parser = argparse.ArgumentParser(description='G2 Programming Language', 
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog="""
Examples:
  g2 run hello.g2              # Run a G2 file
  g2 run hello.g2 --debug      # Run with debug output
  g2 repl                      # Start interactive REPL
  g2 compile hello.g2          # Compile to bytecode
  g2 ast hello.g2              # Show AST
  g2 tokens hello.g2           # Show tokens
  g2 cache clear               # Clear cache
""")
    
    parser.add_argument('command', nargs='?', default='repl',
                        choices=['run', 'repl', 'compile', 'ast', 'tokens', 'cache'],
                        help='Command to execute')
    parser.add_argument('file', nargs='?', help='G2 source file')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--no-cache', action='store_true', help='Disable caching')
    
    args = parser.parse_args()
    
    cli = G2CLI()
    cli.debug = args.debug
    
    if args.command == 'repl':
        cli.run_repl()
    elif args.command == 'run':
        if args.file:
            cli.run_file(args.file, use_cache=not args.no_cache)
        else:
            print("Error: Please specify a file to run")
            sys.exit(1)
    elif args.command == 'compile':
        if args.file:
            cli.compile_file(args.file)
        else:
            print("Error: Please specify a file to compile")
            sys.exit(1)
    elif args.command == 'ast':
        if args.file:
            cli.show_ast(args.file)
        else:
            print("Error: Please specify a file")
            sys.exit(1)
    elif args.command == 'tokens':
        if args.file:
            cli.show_tokens(args.file)
        else:
            print("Error: Please specify a file")
            sys.exit(1)
    elif args.command == 'cache':
        if args.file == 'clear':
            cli.clear_cache()
        else:
            print("Usage: g2 cache clear")
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()