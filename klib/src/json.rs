//! 외부 의존성 없는 경량 JSON 파서 및 직렬화 모듈.
//! RFC 8259 문법 및 UTF-16 대리 쌍(surrogate pair) 처리 지원.

use std::fmt::Write;

#[derive(Debug, Clone, PartialEq)]
pub enum Value {
    Null,
    Bool(bool),
    Num(f64),
    Str(String),
    Arr(Vec<Value>),
    Obj(Vec<(String, Value)>),
}

impl Value {
    pub fn get(&self, key: &str) -> Option<&Value> {
        match self {
            Value::Obj(items) => items.iter().find(|(k, _)| k == key).map(|(_, v)| v),
            _ => None,
        }
    }
    pub fn str(&self, key: &str) -> Option<&str> {
        match self.get(key) {
            Some(Value::Str(s)) => Some(s),
            _ => None,
        }
    }
    pub fn num(&self, key: &str) -> Option<f64> {
        match self.get(key) {
            Some(Value::Num(n)) => Some(*n),
            _ => None,
        }
    }
    pub fn i64(&self, key: &str) -> Option<i64> {
        self.num(key).filter(|n| n.fract() == 0.0).map(|n| *n as i64)
    }
    pub fn bool(&self, key: &str) -> Option<bool> {
        match self.get(key) {
            Some(Value::Bool(b)) => Some(*b),
            _ => None,
        }
    }
    pub fn arr(&self, key: &str) -> Option<&[Value]> {
        match self.get(key) {
            Some(Value::Arr(items)) => Some(items.as_slice()),
            _ => None,
        }
    }
    pub fn obj(items: Vec<(&str, Value)>) -> Value {
        Value::Obj(items.into_iter().map(|(k, v)| (k.to_string(), v)).collect())
    }
}

impl From<&str> for Value {
    fn from(s: &str) -> Self {
        Value::Str(s.to_string())
    }
}
impl From<String> for Value {
    fn from(s: String) -> Self {
        Value::Str(s)
    }
}
impl From<bool> for Value {
    fn from(b: bool) -> Self {
        Value::Bool(b)
    }
}
impl From<f64> for Value {
    fn from(n: f64) -> Self {
        Value::Num(n)
    }
}
impl From<i64> for Value {
    fn from(n: i64) -> Self {
        Value::Num(n as f64)
    }
}
impl From<usize> for Value {
    fn from(n: usize) -> Self {
        Value::Num(n as f64)
    }
}

pub fn to_string(value: &Value) -> String {
    let mut out = String::new();
    write_value(&mut out, value);
    out
}

fn write_value(out: &mut String, value: &Value) {
    match value {
        Value::Null => out.push_str("null"),
        Value::Bool(b) => out.push_str(if *b { "true" } else { "false" }),
        Value::Num(n) => {
            if n.is_finite() && n.fract() == 0.0 && n.abs() < 9.0e15 {
                let _ = write!(out, "{}", *n as i64);
            } else if n.is_finite() {
                let _ = write!(out, "{}", n);
            } else {
                out.push_str("null");
            }
        }
        Value::Str(s) => write_str(out, s),
        Value::Arr(items) => {
            out.push('[');
            for (i, item) in items.iter().enumerate() {
                if i > 0 {
                    out.push(',');
                }
                write_value(out, item);
            }
            out.push(']');
        }
        Value::Obj(items) => {
            out.push('{');
            for (i, (k, v)) in items.iter().enumerate() {
                if i > 0 {
                    out.push(',');
                }
                write_str(out, k);
                out.push(':');
                write_value(out, v);
            }
            out.push('}');
        }
    }
}

fn write_str(out: &mut String, s: &str) {
    out.push('"');
    for ch in s.chars() {
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if (c as u32) < 0x20 => {
                let _ = write!(out, "\\u{:04x}", c as u32);
            }
            c => out.push(c),
        }
    }
    out.push('"');
}

pub fn parse(text: &str) -> Option<Value> {
    let mut p = Parser {
        s: text.as_bytes(),
        i: 0,
        depth: 0,
    };
    let v = p.value()?;
    p.ws();
    if p.i == p.s.len() {
        Some(v)
    } else {
        None
    }
}

struct Parser<'a> {
    s: &'a [u8],
    i: usize,
    depth: u32,
}

impl Parser<'_> {
    fn ws(&mut self) {
        while self.i < self.s.len() && matches!(self.s[self.i], b' ' | b'\t' | b'\n' | b'\r') {
            self.i += 1;
        }
    }
    fn eat(&mut self, lit: &[u8]) -> bool {
        if self.s[self.i..].starts_with(lit) {
            self.i += lit.len();
            true
        } else {
            false
        }
    }
    fn value(&mut self) -> Option<Value> {
        self.ws();
        self.depth += 1;
        if self.depth > 64 {
            return None;
        }
        let first = *self.s.get(self.i)?;
        let v = match first {
            b'n' => self.eat(b"null").then_some(Value::Null),
            b't' => self.eat(b"true").then_some(Value::Bool(true)),
            b'f' => self.eat(b"false").then_some(Value::Bool(false)),
            b'"' => self.string().map(Value::Str),
            b'[' => {
                self.i += 1;
                let mut items = Vec::new();
                self.ws();
                if self.eat(b"]") {
                    Some(Value::Arr(items))
                } else {
                    loop {
                        items.push(self.value()?);
                        self.ws();
                        if self.eat(b",") {
                            continue;
                        }
                        if self.eat(b"]") {
                            break Some(Value::Arr(items));
                        }
                        return None;
                    }
                }
            }
            b'{' => {
                self.i += 1;
                let mut items = Vec::new();
                self.ws();
                if self.eat(b"}") {
                    Some(Value::Obj(items))
                } else {
                    loop {
                        self.ws();
                        let key = self.string()?;
                        self.ws();
                        if !self.eat(b":") {
                            return None;
                        }
                        let v = self.value()?;
                        items.push((key, v));
                        self.ws();
                        if self.eat(b",") {
                            continue;
                        }
                        if self.eat(b"}") {
                            break Some(Value::Obj(items));
                        }
                        return None;
                    }
                }
            }
            b'-' | b'0'..=b'9' => self.number(),
            _ => None,
        };
        self.depth -= 1;
        v
    }
    fn number(&mut self) -> Option<Value> {
        let start = self.i;
        // 1. 선택적 음수 부호 '-' (JSON 문법상 '+' 부호는 허용되지 않음)
        if self.i < self.s.len() && self.s[self.i] == b'-' {
            self.i += 1;
        }

        // 2. 정수부: 첫 번째 숫자
        let first_digit = *self.s.get(self.i)?;
        if !first_digit.is_ascii_digit() {
            return None;
        }
        self.i += 1;
        if first_digit == b'0' {
            // leading zero 금지: 0 뒤에 숫자가 바로 오면 안 됨 (예: 01)
            if self.i < self.s.len() && self.s[self.i].is_ascii_digit() {
                return None;
            }
        } else {
            while self.i < self.s.len() && self.s[self.i].is_ascii_digit() {
                self.i += 1;
            }
        }

        // 3. 소수부 (선택적)
        if self.i < self.s.len() && self.s[self.i] == b'.' {
            self.i += 1;
            let frac_start = self.i;
            while self.i < self.s.len() && self.s[self.i].is_ascii_digit() {
                self.i += 1;
            }
            if self.i == frac_start {
                // 소수점 뒤에 숫자가 없음 (예: "1.")
                return None;
            }
        }

        // 4. 지수부 (선택적)
        if self.i < self.s.len() && matches!(self.s[self.i], b'e' | b'E') {
            self.i += 1;
            if self.i < self.s.len() && matches!(self.s[self.i], b'+' | b'-') {
                self.i += 1;
            }
            let exp_start = self.i;
            while self.i < self.s.len() && self.s[self.i].is_ascii_digit() {
                self.i += 1;
            }
            if self.i == exp_start {
                // 지수 뒤에 숫자가 없음 (예: "1e", "1e+")
                return None;
            }
        }

        let raw = std::str::from_utf8(&self.s[start..self.i]).ok()?;
        raw.parse::<f64>().ok().map(Value::Num)
    }
    fn string(&mut self) -> Option<String> {
        if !self.eat(b"\"") {
            return None;
        }
        let mut bytes: Vec<u8> = Vec::new();
        let mut closed = false;

        while self.i < self.s.len() {
            let b = self.s[self.i];
            self.i += 1;
            match b {
                b'"' => {
                    closed = true;
                    break;
                }
                b'\\' => {
                    let e = *self.s.get(self.i)?;
                    self.i += 1;
                    match e {
                        b'"' => bytes.push(b'"'),
                        b'\\' => bytes.push(b'\\'),
                        b'/' => bytes.push(b'/'),
                        b'b' => bytes.push(8),
                        b'f' => bytes.push(12),
                        b'n' => bytes.push(b'\n'),
                        b'r' => bytes.push(b'\r'),
                        b't' => bytes.push(b'\t'),
                        b'u' => {
                            let u1 = self.hex4()?;
                            if (0xD800..=0xDBFF).contains(&u1) {
                                // High surrogate: 반드시 이어서 \uDC00..\uDFFF (Low surrogate)가 와야 함
                                if !self.eat(b"\\u") {
                                    return None;
                                }
                                let u2 = self.hex4()?;
                                if !(0xDC00..=0xDFFF).contains(&u2) {
                                    return None;
                                }
                                let mut iter = char::decode_utf16([u1, u2]);
                                let ch = iter.next()?.ok()?;
                                let mut buf = [0u8; 4];
                                bytes.extend_from_slice(ch.encode_utf8(&mut buf).as_bytes());
                            } else if (0xDC00..=0xDFFF).contains(&u1) {
                                // 단독 Low surrogate는 유효하지 않음
                                return None;
                            } else {
                                let ch = char::from_u32(u1 as u32)?;
                                let mut buf = [0u8; 4];
                                bytes.extend_from_slice(ch.encode_utf8(&mut buf).as_bytes());
                            }
                        }
                        _ => return None,
                    }
                }
                // RFC 8259: 0x00..=0x1F 제어 문자는 문자열 리터럴에 이스케이프 없이 올 수 없음
                0x00..=0x1F => return None,
                _ => bytes.push(b),
            }
        }

        if !closed {
            return None;
        }

        String::from_utf8(bytes).ok()
    }

    fn hex4(&mut self) -> Option<u16> {
        if self.i + 4 > self.s.len() {
            return None;
        }
        let hex_slice = &self.s[self.i..self.i + 4];
        for &b in hex_slice {
            if !b.is_ascii_hexdigit() {
                return None;
            }
        }
        let hex_str = std::str::from_utf8(hex_slice).ok()?;
        self.i += 4;
        u16::from_str_radix(hex_str, 16).ok()
    }
}
