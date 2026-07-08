#[derive(Debug, Clone, PartialEq)]
enum Token {
    Number(f64),
    Column(String),
    Plus,
    Minus,
    Star,
    Slash,
    LParen,
    RParen,
}

pub fn evaluate_formula(
    formula: &str,
    headers: &[String],
    row: &[String],
) -> Result<f64, String> {
    let tokens = tokenize(formula)?;
    if tokens.is_empty() {
        return Err("Formula cannot be empty".to_owned());
    }

    let mut parser = Parser {
        tokens,
        position: 0,
        headers,
        row,
    };
    let value = parser.parse_expression()?;
    if parser.position != parser.tokens.len() {
        return Err("Unexpected trailing tokens in formula".to_owned());
    }

    if !value.is_finite() {
        return Err("Formula evaluated to a non-finite value".to_owned());
    }

    Ok(value)
}

pub fn format_number(value: f64) -> String {
    if (value - value.round()).abs() < f64::EPSILON {
        format!("{}", value.round() as i64)
    } else {
        let mut text = format!("{value}");
        if text.contains('.') {
            while text.ends_with('0') {
                text.pop();
            }
            if text.ends_with('.') {
                text.pop();
            }
        }
        text
    }
}

struct Parser<'a> {
    tokens: Vec<Token>,
    position: usize,
    headers: &'a [String],
    row: &'a [String],
}

impl<'a> Parser<'a> {
    fn parse_expression(&mut self) -> Result<f64, String> {
        let mut value = self.parse_term()?;
        loop {
            match self.peek() {
                Some(Token::Plus) => {
                    self.advance();
                    value += self.parse_term()?;
                }
                Some(Token::Minus) => {
                    self.advance();
                    value -= self.parse_term()?;
                }
                _ => break,
            }
        }
        Ok(value)
    }

    fn parse_term(&mut self) -> Result<f64, String> {
        let mut value = self.parse_unary()?;
        loop {
            match self.peek() {
                Some(Token::Star) => {
                    self.advance();
                    value *= self.parse_unary()?;
                }
                Some(Token::Slash) => {
                    self.advance();
                    let divisor = self.parse_unary()?;
                    if divisor.abs() <= f64::EPSILON {
                        return Err("Division by zero".to_owned());
                    }
                    value /= divisor;
                }
                _ => break,
            }
        }
        Ok(value)
    }

    fn parse_unary(&mut self) -> Result<f64, String> {
        match self.peek() {
            Some(Token::Minus) => {
                self.advance();
                Ok(-self.parse_unary()?)
            }
            _ => self.parse_primary(),
        }
    }

    fn parse_primary(&mut self) -> Result<f64, String> {
        match self.advance() {
            Some(Token::Number(value)) => Ok(value),
            Some(Token::Column(name)) => self.resolve_column_value(&name),
            Some(Token::LParen) => {
                let value = self.parse_expression()?;
                match self.advance() {
                    Some(Token::RParen) => Ok(value),
                    _ => Err("Missing closing ')' in formula".to_owned()),
                }
            }
            Some(token) => Err(format!("Unexpected token {:?} in formula", token)),
            None => Err("Unexpected end of formula".to_owned()),
        }
    }

    fn resolve_column_value(&self, column_name: &str) -> Result<f64, String> {
        let index = self
            .headers
            .iter()
            .position(|header| header == column_name)
            .ok_or_else(|| format!("Unknown column '{column_name}'"))?;
        let value = self
            .row
            .get(index)
            .ok_or_else(|| format!("Column '{column_name}' has no value in this row"))?;
        let value = value.trim();
        if value.is_empty() {
            return Err(format!("Column '{column_name}' is empty in this row"));
        }
        value
            .parse::<f64>()
            .map_err(|_| format!("Column '{column_name}' is not numeric in this row"))
    }

    fn peek(&self) -> Option<&Token> {
        self.tokens.get(self.position)
    }

    fn advance(&mut self) -> Option<Token> {
        let token = self.tokens.get(self.position).cloned();
        if token.is_some() {
            self.position += 1;
        }
        token
    }
}

fn tokenize(formula: &str) -> Result<Vec<Token>, String> {
    let mut tokens = Vec::new();
    let mut chars = formula.chars().peekable();

    while let Some(ch) = chars.peek().copied() {
        if ch.is_whitespace() {
            chars.next();
            continue;
        }

        match ch {
            '+' => {
                chars.next();
                tokens.push(Token::Plus);
            }
            '-' => {
                chars.next();
                tokens.push(Token::Minus);
            }
            '*' => {
                chars.next();
                tokens.push(Token::Star);
            }
            '/' => {
                chars.next();
                tokens.push(Token::Slash);
            }
            '(' => {
                chars.next();
                tokens.push(Token::LParen);
            }
            ')' => {
                chars.next();
                tokens.push(Token::RParen);
            }
            '\'' | '`' => {
                let quote = ch;
                chars.next();
                let mut name = String::new();
                let mut closed = false;
                while let Some(next) = chars.next() {
                    if next == quote {
                        closed = true;
                        break;
                    }
                    name.push(next);
                }
                if !closed {
                    return Err("Unterminated column reference in formula".to_owned());
                }
                if name.is_empty() {
                    return Err("Column reference cannot be empty".to_owned());
                }
                tokens.push(Token::Column(name));
            }
            _ if ch.is_ascii_digit() || ch == '.' => {
                let mut text = String::new();
                let mut saw_exponent = false;
                while let Some(next) = chars.peek().copied() {
                    if next.is_ascii_digit() || next == '.' {
                        text.push(next);
                        chars.next();
                    } else if (next == 'e' || next == 'E') && !saw_exponent {
                        saw_exponent = true;
                        text.push(next);
                        chars.next();
                        if let Some(sign) = chars.peek().copied()
                            && (sign == '+' || sign == '-')
                        {
                            text.push(sign);
                            chars.next();
                        }
                    } else {
                        break;
                    }
                }
                let value = text
                    .parse::<f64>()
                    .map_err(|_| format!("Invalid numeric literal '{text}'"))?;
                tokens.push(Token::Number(value));
            }
            _ if ch.is_ascii_alphabetic() || ch == '_' => {
                let mut name = String::new();
                while let Some(next) = chars.peek().copied() {
                    if next.is_ascii_alphanumeric() || next == '_' {
                        name.push(next);
                        chars.next();
                    } else {
                        break;
                    }
                }
                tokens.push(Token::Column(name));
            }
            _ => {
                return Err(format!("Unexpected character '{ch}' in formula"));
            }
        }
    }

    Ok(tokens)
}
