use pyo3::prelude::*;
use pythonize::{depythonize, pythonize};
use serde_json::Value;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ToonError {
    #[error("Encoding error: {0}")]
    EncodingError(String),
    #[error("Decoding error: {0}")]
    DecodingError(String),
    #[error("Invalid delimiter: {0}")]
    InvalidDelimiter(String),
    #[error("Python conversion error: {0}")]
    PythonError(String),
}

impl From<ToonError> for PyErr {
    fn from(err: ToonError) -> PyErr {
        pyo3::exceptions::PyValueError::new_err(err.to_string())
    }
}

/// Configuration options for TOON encoding
#[pyclass]
#[derive(Clone)]
pub struct EncodeOptions {
    #[pyo3(get, set)]
    pub delimiter: String,
    #[pyo3(get, set)]
    pub indent: usize,
    #[pyo3(get, set)]
    pub use_length_markers: bool,
    #[pyo3(get, set)]
    pub strict: bool,
}

#[pymethods]
impl EncodeOptions {
    #[new]
    #[pyo3(signature = (delimiter=",".to_string(), indent=2, use_length_markers=true, strict=true))]
    fn new(delimiter: String, indent: usize, use_length_markers: bool, strict: bool) -> Self {
        EncodeOptions {
            delimiter,
            indent,
            use_length_markers,
            strict,
        }
    }
}

impl Default for EncodeOptions {
    fn default() -> Self {
        EncodeOptions {
            delimiter: ",".to_string(),
            indent: 2,
            use_length_markers: true,
            strict: true,
        }
    }
}

/// Configuration options for TOON decoding
#[pyclass]
#[derive(Clone)]
pub struct DecodeOptions {
    #[pyo3(get, set)]
    pub strict: bool,
}

#[pymethods]
impl DecodeOptions {
    #[new]
    #[pyo3(signature = (strict=true,))]
    fn new(strict: bool) -> Self {
        DecodeOptions { strict }
    }
}

impl Default for DecodeOptions {
    fn default() -> Self {
        DecodeOptions { strict: true }
    }
}

/// Check if a string needs quoting according to TOON rules
fn needs_quoting(s: &str, delimiter: &str) -> bool {
    if s.is_empty() {
        return true;
    }

    // Check for leading/trailing whitespace
    if s.starts_with(' ') || s.ends_with(' ') {
        return true;
    }

    // Check for reserved words
    if matches!(s, "true" | "false" | "null") {
        return true;
    }

    // Check if it looks like a number
    if s.parse::<f64>().is_ok() || s.starts_with('0') && s.len() > 1 && s.chars().nth(1) != Some('.') {
        return true;
    }

    // Check for special characters
    for ch in s.chars() {
        if matches!(ch, ':' | '"' | '\\' | '\n' | '\r' | '\t' | '[' | ']' | '{' | '}' | '-') {
            return true;
        }
        if ch.is_control() {
            return true;
        }
    }

    // Check for delimiter
    if s.contains(delimiter) {
        return true;
    }

    false
}

/// Escape a string for TOON format
fn escape_string(s: &str) -> String {
    let mut result = String::new();
    for ch in s.chars() {
        match ch {
            '\\' => result.push_str("\\\\"),
            '"' => result.push_str("\\\""),
            '\n' => result.push_str("\\n"),
            '\r' => result.push_str("\\r"),
            '\t' => result.push_str("\\t"),
            _ => result.push(ch),
        }
    }
    result
}

/// Quote a string if needed
fn quote_if_needed(s: &str, delimiter: &str) -> String {
    if needs_quoting(s, delimiter) {
        format!("\"{}\"", escape_string(s))
    } else {
        s.to_string()
    }
}

/// Check if a key is a valid identifier (doesn't need quoting)
fn is_valid_identifier(s: &str) -> bool {
    if s.is_empty() {
        return false;
    }

    let mut chars = s.chars();
    let first = chars.next().unwrap();

    if !matches!(first, 'A'..='Z' | 'a'..='z' | '_') {
        return false;
    }

    for ch in chars {
        if !matches!(ch, 'A'..='Z' | 'a'..='z' | '0'..='9' | '_' | '.') {
            return false;
        }
    }

    true
}

/// Check if array contains uniform objects (all same keys, all primitive values)
fn is_uniform_object_array(arr: &[Value]) -> Option<Vec<String>> {
    if arr.is_empty() {
        return None;
    }

    let first = arr.first()?;
    if !first.is_object() {
        return None;
    }

    let first_obj = first.as_object()?;
    let keys: Vec<String> = first_obj.keys().cloned().collect();

    // Check all values are primitives
    for val in first_obj.values() {
        if val.is_object() || val.is_array() {
            return None;
        }
    }

    // Check all other objects have same keys and primitive values
    for item in &arr[1..] {
        if !item.is_object() {
            return None;
        }
        let obj = item.as_object()?;

        if obj.len() != keys.len() {
            return None;
        }

        for key in &keys {
            if !obj.contains_key(key) {
                return None;
            }
            let val = &obj[key];
            if val.is_object() || val.is_array() {
                return None;
            }
        }
    }

    Some(keys)
}

/// Encode a value to TOON format
fn encode_value(
    value: &Value,
    indent_level: usize,
    options: &EncodeOptions,
) -> Result<String, ToonError> {
    let indent = " ".repeat(indent_level * options.indent);

    match value {
        Value::Null => Ok("null".to_string()),
        Value::Bool(b) => Ok(b.to_string()),
        Value::Number(n) => {
            // Normalize numbers: no exponent, no trailing zeros
            if let Some(i) = n.as_i64() {
                Ok(i.to_string())
            } else if let Some(f) = n.as_f64() {
                let s = format!("{}", f);
                // Remove trailing zeros after decimal point
                if s.contains('.') {
                    let trimmed = s.trim_end_matches('0').trim_end_matches('.');
                    Ok(trimmed.to_string())
                } else {
                    Ok(s)
                }
            } else {
                Ok(n.to_string())
            }
        }
        Value::String(s) => Ok(quote_if_needed(s, &options.delimiter)),
        Value::Array(arr) => {
            if arr.is_empty() {
                return Ok(format!("[0]:"));
            }

            // Check if it's a uniform object array (tabular format)
            if let Some(keys) = is_uniform_object_array(arr) {
                let mut result = String::new();

                // Header: [N,]{key1,key2,...}:
                let delim_marker = if options.delimiter == "," {
                    ""
                } else if options.delimiter == "\t" {
                    "\t"
                } else if options.delimiter == "|" {
                    "|"
                } else {
                    return Err(ToonError::InvalidDelimiter(options.delimiter.clone()));
                };

                if options.use_length_markers {
                    result.push_str(&format!("[{}{delim_marker}]", arr.len()));
                } else {
                    result.push_str("[]");
                }

                result.push('{');
                for (i, key) in keys.iter().enumerate() {
                    if i > 0 {
                        result.push_str(&options.delimiter);
                    }
                    result.push_str(key);
                }
                result.push_str("}:\n");

                // Data rows
                for obj_val in arr {
                    result.push_str(&indent);
                    result.push_str(&" ".repeat(options.indent));

                    let obj = obj_val.as_object().unwrap();
                    for (i, key) in keys.iter().enumerate() {
                        if i > 0 {
                            result.push_str(&options.delimiter);
                        }
                        let val = &obj[key];
                        let val_str = encode_value(val, 0, options)?;
                        result.push_str(&val_str);
                    }
                    result.push('\n');
                }

                return Ok(result.trim_end().to_string());
            }

            // Check if all elements are primitives (inline array)
            let all_primitives = arr.iter().all(|v| !v.is_object() && !v.is_array());

            if all_primitives {
                // Inline format: [N,]: val1,val2,val3
                let mut result = String::new();

                let delim_marker = if options.delimiter == "," {
                    ""
                } else if options.delimiter == "\t" {
                    "\t"
                } else if options.delimiter == "|" {
                    "|"
                } else {
                    return Err(ToonError::InvalidDelimiter(options.delimiter.clone()));
                };

                if options.use_length_markers {
                    result.push_str(&format!("[{}{delim_marker}]: ", arr.len()));
                } else {
                    result.push_str("[]: ");
                }

                for (i, val) in arr.iter().enumerate() {
                    if i > 0 {
                        result.push_str(&options.delimiter);
                    }
                    result.push_str(&encode_value(val, 0, options)?);
                }

                return Ok(result);
            }

            // Mixed/nested array (expanded format with -)
            let mut result = String::new();

            let delim_marker = if options.delimiter == "," {
                ""
            } else if options.delimiter == "\t" {
                "\t"
            } else if options.delimiter == "|" {
                "|"
            } else {
                return Err(ToonError::InvalidDelimiter(options.delimiter.clone()));
            };

            if options.use_length_markers {
                result.push_str(&format!("[{}{delim_marker}]:\n", arr.len()));
            } else {
                result.push_str("[]:\n");
            }

            for val in arr {
                result.push_str(&indent);
                result.push_str(&" ".repeat(options.indent));
                result.push_str("- ");

                if val.is_object() {
                    let obj = val.as_object().unwrap();
                    let mut first = true;
                    for (key, v) in obj {
                        if !first {
                            result.push('\n');
                            result.push_str(&indent);
                            result.push_str(&" ".repeat(options.indent * 2));
                        }
                        first = false;

                        let key_str = if is_valid_identifier(key) {
                            key.clone()
                        } else {
                            quote_if_needed(key, &options.delimiter)
                        };

                        if v.is_object() || v.is_array() {
                            result.push_str(&format!("{}:\n", key_str));
                            let nested = encode_value(v, indent_level + 2, options)?;
                            for line in nested.lines() {
                                result.push_str(&indent);
                                result.push_str(&" ".repeat(options.indent * 2));
                                result.push_str(line);
                                result.push('\n');
                            }
                        } else {
                            result.push_str(&format!("{}: {}", key_str, encode_value(v, 0, options)?));
                        }
                    }
                    result.push('\n');
                } else {
                    result.push_str(&encode_value(val, 0, options)?);
                    result.push('\n');
                }
            }

            Ok(result.trim_end().to_string())
        }
        Value::Object(obj) => {
            if obj.is_empty() {
                return Ok(String::new());
            }

            let mut result = String::new();

            for (i, (key, val)) in obj.iter().enumerate() {
                if i > 0 {
                    result.push('\n');
                }

                result.push_str(&indent);

                let key_str = if is_valid_identifier(key) {
                    key.clone()
                } else {
                    quote_if_needed(key, &options.delimiter)
                };

                if val.is_object() || val.is_array() {
                    result.push_str(&format!("{}:\n", key_str));
                    let nested = encode_value(val, indent_level + 1, options)?;
                    for line in nested.lines() {
                        result.push_str(&indent);
                        result.push_str(&" ".repeat(options.indent));
                        result.push_str(line);
                        result.push('\n');
                    }
                    result = result.trim_end().to_string();
                } else {
                    result.push_str(&format!("{}: {}", key_str, encode_value(val, 0, options)?));
                }
            }

            Ok(result)
        }
    }
}

/// Unescape a TOON string
fn unescape_string(s: &str) -> Result<String, ToonError> {
    let mut result = String::new();
    let mut chars = s.chars();

    while let Some(ch) = chars.next() {
        if ch == '\\' {
            match chars.next() {
                Some('\\') => result.push('\\'),
                Some('"') => result.push('"'),
                Some('n') => result.push('\n'),
                Some('r') => result.push('\r'),
                Some('t') => result.push('\t'),
                Some(other) => {
                    return Err(ToonError::DecodingError(format!(
                        "Invalid escape sequence: \\{}",
                        other
                    )))
                }
                None => {
                    return Err(ToonError::DecodingError(
                        "Unterminated escape sequence".to_string(),
                    ))
                }
            }
        } else {
            result.push(ch);
        }
    }

    Ok(result)
}

/// Parse a value from a TOON string
fn parse_value(s: &str, _delimiter: &str) -> Result<Value, ToonError> {
    let s = s.trim();

    if s.is_empty() {
        return Ok(Value::String(String::new()));
    }

    // Quoted string
    if s.starts_with('"') && s.ends_with('"') {
        let inner = &s[1..s.len() - 1];
        return Ok(Value::String(unescape_string(inner)?));
    }

    // Boolean
    if s == "true" {
        return Ok(Value::Bool(true));
    }
    if s == "false" {
        return Ok(Value::Bool(false));
    }

    // Null
    if s == "null" {
        return Ok(Value::Null);
    }

    // Number
    if let Ok(i) = s.parse::<i64>() {
        return Ok(Value::Number(i.into()));
    }
    if let Ok(f) = s.parse::<f64>() {
        if let Some(n) = serde_json::Number::from_f64(f) {
            return Ok(Value::Number(n));
        }
    }

    // Otherwise, it's a string
    Ok(Value::String(s.to_string()))
}

/// Decode TOON format to JSON Value
pub fn decode(toon_str: &str, _options: &DecodeOptions) -> Result<Value, ToonError> {
    let lines: Vec<&str> = toon_str.lines().collect();

    if lines.is_empty() {
        return Ok(Value::Object(serde_json::Map::new()));
    }

    // Simple implementation for basic cases
    // This is a simplified decoder for the MVP
    let mut result = serde_json::Map::new();
    let delimiter = ","; // Default delimiter
    let mut pending_key: Option<String> = None;

    let mut i = 0;
    while i < lines.len() {
        let line = lines[i].trim_end();

        if line.is_empty() {
            i += 1;
            continue;
        }

        // Check for key: value pattern
        if let Some(colon_pos) = line.find(':') {
            let key_part = line[..colon_pos].trim();
            let value_part = line[colon_pos + 1..].trim();

            // Array header pattern: key[N]{...}: or key[N]:
            if key_part.contains('[') {
                let bracket_start = key_part.find('[').unwrap();
                let mut key = key_part[..bracket_start].trim().to_string();

                // If key is empty and we have a pending key (nested structure), use it
                if key.is_empty() && pending_key.is_some() {
                    key = pending_key.take().unwrap();
                }

                // Check for tabular array {fields}:
                if key_part.contains('{') && value_part.is_empty() {
                    let fields_start = key_part.find('{').unwrap();
                    let fields_end = key_part.find('}').unwrap();
                    let fields_str = &key_part[fields_start + 1..fields_end];
                    let fields: Vec<&str> = fields_str.split(delimiter).map(|s| s.trim()).collect();

                    // Read data rows
                    let mut rows = Vec::new();
                    i += 1;
                    while i < lines.len() {
                        let data_line = lines[i];
                        if data_line.trim().is_empty() || (!data_line.starts_with(' ') && !data_line.starts_with('\t')) {
                            break;
                        }

                        let data_line = data_line.trim();
                        let values: Vec<&str> = data_line.split(delimiter).collect();

                        let mut row_obj = serde_json::Map::new();
                        for (field, value) in fields.iter().zip(values.iter()) {
                            row_obj.insert(field.to_string(), parse_value(value, delimiter)?);
                        }
                        rows.push(Value::Object(row_obj));
                        i += 1;
                    }

                    result.insert(key, Value::Array(rows));
                    pending_key = None;
                    continue;
                }

                // Inline primitive array: key[N]: val1,val2,val3
                if !value_part.is_empty() {
                    let values: Vec<Value> = value_part
                        .split(delimiter)
                        .map(|s| parse_value(s.trim(), delimiter))
                        .collect::<Result<Vec<_>, _>>()?;
                    result.insert(key, Value::Array(values));
                    pending_key = None;
                    i += 1;
                    continue;
                }

                // Array without inline values - might have data on next lines
                i += 1;
                continue;
            }

            // Simple key: value
            if !value_part.is_empty() {
                let key = if key_part.starts_with('"') && key_part.ends_with('"') {
                    unescape_string(&key_part[1..key_part.len() - 1])?
                } else {
                    key_part.to_string()
                };
                result.insert(key, parse_value(value_part, delimiter)?);
                pending_key = None;
            } else {
                // Key with empty value - might be parent of nested structure
                pending_key = Some(key_part.to_string());
            }
        }

        i += 1;
    }

    Ok(Value::Object(result))
}

/// Encode Python data to TOON format
#[pyfunction]
#[pyo3(signature = (data, options=None))]
pub fn encode(_py: Python, data: &Bound<'_, PyAny>, options: Option<&EncodeOptions>) -> PyResult<String> {
    let opts = options.cloned().unwrap_or_default();

    // Convert Python object to serde_json::Value
    let value: Value = depythonize(data)
        .map_err(|e| ToonError::PythonError(e.to_string()))?;

    // Encode to TOON
    let result = encode_value(&value, 0, &opts)
        .map_err(|e| PyErr::from(e))?;

    Ok(result)
}

/// Decode TOON format to Python data
#[pyfunction]
#[pyo3(signature = (toon_str, options=None))]
pub fn decode_toon(py: Python, toon_str: &str, options: Option<&DecodeOptions>) -> PyResult<PyObject> {
    let opts = options.cloned().unwrap_or_default();

    // Decode from TOON
    let value = decode(toon_str, &opts)
        .map_err(|e| PyErr::from(e))?;

    // Convert to Python object
    let py_obj = pythonize(py, &value)
        .map_err(|e| ToonError::PythonError(e.to_string()))?;

    Ok(py_obj.unbind())
}

/// Python module
#[pymodule]
fn _toon_tuna(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(encode, m)?)?;
    m.add_function(wrap_pyfunction!(decode_toon, m)?)?;
    m.add_class::<EncodeOptions>()?;
    m.add_class::<DecodeOptions>()?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_quote_if_needed() {
        let opts = EncodeOptions::default();
        assert_eq!(quote_if_needed("hello", &opts.delimiter), "hello");
        assert_eq!(quote_if_needed("hello world", &opts.delimiter), "\"hello world\"");
        assert_eq!(quote_if_needed("true", &opts.delimiter), "\"true\"");
        assert_eq!(quote_if_needed("123", &opts.delimiter), "\"123\"");
    }

    #[test]
    fn test_encode_simple_object() {
        let data = serde_json::json!({
            "id": 123,
            "name": "Alice"
        });

        let opts = EncodeOptions::default();
        let result = encode_value(&data, 0, &opts).unwrap();

        assert!(result.contains("id: 123"));
        assert!(result.contains("name: Alice"));
    }

    #[test]
    fn test_encode_tabular_array() {
        let data = serde_json::json!({
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ]
        });

        let opts = EncodeOptions::default();
        let result = encode_value(&data, 0, &opts).unwrap();

        assert!(result.contains("[2,]{id,name}:"));
        assert!(result.contains("1,Alice"));
        assert!(result.contains("2,Bob"));
    }

    #[test]
    fn test_encode_primitive_array() {
        let data = serde_json::json!({
            "tags": [1, 2, 3]
        });

        let opts = EncodeOptions::default();
        let result = encode_value(&data, 0, &opts).unwrap();

        assert!(result.contains("tags:"));
        assert!(result.contains("[3,]: 1,2,3"));
    }
}
