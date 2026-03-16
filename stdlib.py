import time
import math
import random
import sys
import os
import json
import re
from typing import Any, List, Dict, Optional
from datetime import datetime
sys.dont_write_bytecode = True
class G2StdLib:
    """Standard library for G2 language"""
    
    # I/O Functions
    @staticmethod
    def print(*args, **kwargs):
        """Print to console"""
        output = ' '.join(str(arg) for arg in args)
        print(output, **kwargs)
        return None
    
    @staticmethod
    def println(*args, **kwargs):
        """Print with newline"""
        G2StdLib.print(*args, **kwargs, end='\n')
    
    @staticmethod
    def input(prompt: str = "") -> str:
        """Get user input"""
        return input(str(prompt))
    
    @staticmethod
    def printf(format_str: str, *args):
        """Formatted print"""
        print(format_str % args, end='')
    
    # Type conversion
    @staticmethod
    def to_int(value: Any) -> int:
        """Convert to integer"""
        return int(value)
    
    @staticmethod
    def to_float(value: Any) -> float:
        """Convert to float"""
        return float(value)
    
    @staticmethod
    def to_str(value: Any) -> str:
        """Convert to string"""
        return str(value)
    
    @staticmethod
    def to_bool(value: Any) -> bool:
        """Convert to boolean"""
        return bool(value)
    
    @staticmethod
    def to_list(value: Any) -> list:
        """Convert to list"""
        return list(value) if value else []
    
    # Collections
    @staticmethod
    def len(obj) -> int:
        """Get length"""
        return len(obj)
    
    @staticmethod
    def range(start, stop=None, step=1):
        """Create range"""
        if stop is None:
            return list(range(start))
        return list(range(start, stop, step))
    
    @staticmethod
    def append(lst: list, item: Any) -> list:
        """Append to list"""
        lst.append(item)
        return lst
    
    @staticmethod
    def extend(lst: list, items: list) -> list:
        """Extend list"""
        lst.extend(items)
        return lst
    
    @staticmethod
    def insert(lst: list, index: int, item: Any) -> list:
        """Insert into list"""
        lst.insert(index, item)
        return lst
    
    @staticmethod
    def remove(lst: list, item: Any) -> list:
        """Remove from list"""
        lst.remove(item)
        return lst
    
    @staticmethod
    def pop(lst: list, index: int = -1) -> Any:
        """Pop from list"""
        return lst.pop(index)
    
    @staticmethod
    def sort(lst: list, reverse: bool = False) -> list:
        """Sort list"""
        lst.sort(reverse=reverse)
        return lst
    
    @staticmethod
    def reverse(lst: list) -> list:
        """Reverse list"""
        lst.reverse()
        return lst
    
    @staticmethod
    def map(func, lst: list) -> list:
        """Map function over list"""
        return [func(x) for x in lst]
    
    @staticmethod
    def filter(func, lst: list) -> list:
        """Filter list"""
        return [x for x in lst if func(x)]
    
    @staticmethod
    def reduce(func, lst: list, initial=None):
        """Reduce list"""
        if not lst:
            return initial
        result = lst[0] if initial is None else initial
        for x in lst[1:]:
            result = func(result, x)
        return result
    
    # String functions
    @staticmethod
    def split(s: str, sep: str = None) -> list:
        """Split string"""
        return s.split(sep) if sep else s.split()
    
    @staticmethod
    def join(sep: str, items: list) -> str:
        """Join strings"""
        return sep.join(str(x) for x in items)
    
    @staticmethod
    def replace(s: str, old: str, new: str) -> str:
        """Replace substring"""
        return s.replace(old, new)
    
    @staticmethod
    def upper(s: str) -> str:
        """Convert to uppercase"""
        return s.upper()
    
    @staticmethod
    def lower(s: str) -> str:
        """Convert to lowercase"""
        return s.lower()
    
    @staticmethod
    def strip(s: str) -> str:
        """Strip whitespace"""
        return s.strip()
    
    @staticmethod
    def startswith(s: str, prefix: str) -> bool:
        """Check prefix"""
        return s.startswith(prefix)
    
    @staticmethod
    def endswith(s: str, suffix: str) -> bool:
        """Check suffix"""
        return s.endswith(suffix)
    
    @staticmethod
    def contains(s: str, substr: str) -> bool:
        """Check substring"""
        return substr in s
    
    @staticmethod
    def find(s: str, substr: str) -> int:
        """Find substring"""
        return s.find(substr)
    
    @staticmethod
    def format(s: str, **kwargs) -> str:
        """Format string"""
        return s.format(**kwargs)
    
    # Math functions
    @staticmethod
    def abs(x) -> float:
        return abs(x)
    
    @staticmethod
    def min(*args) -> Any:
        return min(args)
    
    @staticmethod
    def max(*args) -> Any:
        return max(args)
    
    @staticmethod
    def sum(iterable) -> float:
        return sum(iterable)
    
    @staticmethod
    def round(x, ndigits=None) -> float:
        return round(x, ndigits) if ndigits else round(x)
    
    @staticmethod
    def floor(x) -> int:
        return math.floor(x)
    
    @staticmethod
    def ceil(x) -> int:
        return math.ceil(x)
    
    @staticmethod
    def sin(x) -> float:
        return math.sin(x)
    
    @staticmethod
    def cos(x) -> float:
        return math.cos(x)
    
    @staticmethod
    def tan(x) -> float:
        return math.tan(x)
    
    @staticmethod
    def asin(x) -> float:
        return math.asin(x)
    
    @staticmethod
    def acos(x) -> float:
        return math.acos(x)
    
    @staticmethod
    def atan(x) -> float:
        return math.atan(x)
    
    @staticmethod
    def sqrt(x) -> float:
        return math.sqrt(x)
    
    @staticmethod
    def pow(x, y) -> float:
        return math.pow(x, y)
    
    @staticmethod
    def exp(x) -> float:
        return math.exp(x)
    
    @staticmethod
    def log(x, base=math.e) -> float:
        return math.log(x, base)
    
    @staticmethod
    def log10(x) -> float:
        return math.log10(x)
    
    # Random functions
    @staticmethod
    def random() -> float:
        return random.random()
    
    @staticmethod
    def randint(a: int, b: int) -> int:
        return random.randint(a, b)
    
    @staticmethod
    def uniform(a: float, b: float) -> float:
        return random.uniform(a, b)
    
    @staticmethod
    def choice(seq: list) -> Any:
        return random.choice(seq)
    
    @staticmethod
    def shuffle(seq: list) -> list:
        random.shuffle(seq)
        return seq
    
    @staticmethod
    def sample(population: list, k: int) -> list:
        return random.sample(population, k)
    
    # Time functions
    @staticmethod
    def now() -> str:
        return datetime.now().isoformat()
    
    @staticmethod
    def timestamp() -> float:
        return time.time()
    
    @staticmethod
    def sleep(seconds: float):
        time.sleep(seconds)
    
    @staticmethod
    def clock() -> float:
        return time.perf_counter()
    
    # System functions
    @staticmethod
    def exit(code: int = 0):
        sys.exit(code)
    
    @staticmethod
    def env(name: str) -> str:
        return os.environ.get(name, "")
    
    @staticmethod
    def cwd() -> str:
        return os.getcwd()
    
    @staticmethod
    def listdir(path: str = ".") -> list:
        return os.listdir(path)
    
    @staticmethod
    def exists(path: str) -> bool:
        return os.path.exists(path)
    
    # JSON functions
    @staticmethod
    def json_encode(obj) -> str:
        return json.dumps(obj)
    
    @staticmethod
    def json_decode(s: str) -> Any:
        return json.loads(s)
    
    # Regex functions
    @staticmethod
    def match(pattern: str, string: str) -> bool:
        return bool(re.match(pattern, string))
    
    @staticmethod
    def search(pattern: str, string: str) -> Optional[str]:
        match = re.search(pattern, string)
        return match.group() if match else None
    
    @staticmethod
    def findall(pattern: str, string: str) -> list:
        return re.findall(pattern, string)
    
    @staticmethod
    def sub(pattern: str, repl: str, string: str) -> str:
        return re.sub(pattern, repl, string)

def get_stdlib():
    """Get all standard library functions and constants"""
    stdlib = {}
    
    # Add all static methods
    for name in dir(G2StdLib):
        if not name.startswith('_'):
            method = getattr(G2StdLib, name)
            if callable(method):
                stdlib[name] = method
    
    # Add constants
    stdlib['true'] = True
    stdlib['false'] = False
    stdlib['none'] = None
    stdlib['pi'] = math.pi
    stdlib['e'] = math.e
    stdlib['inf'] = float('inf')
    stdlib['nan'] = float('nan')
    
    return stdlib