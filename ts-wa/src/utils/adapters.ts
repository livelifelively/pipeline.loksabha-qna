import { snakeCase, camelCase } from 'lodash';

// Use at I/O boundaries when reading Python-formatted data
export function fromPythonFormat(data: any): any {
  if (Array.isArray(data)) {
    return data.map(fromPythonFormat);
  }

  if (typeof data === 'object' && data !== null) {
    return Object.entries(data).reduce((acc, [key, value]) => {
      acc[camelCase(key)] = fromPythonFormat(value);
      return acc;
    }, {} as any);
  }

  return data;
}

// Use at I/O boundaries when writing data for Python consumption
export function toPythonFormat(data: any): any {
  if (Array.isArray(data)) {
    return data.map(toPythonFormat);
  }

  if (typeof data === 'object' && data !== null) {
    return Object.entries(data).reduce((acc, [key, value]) => {
      acc[snakeCase(key)] = toPythonFormat(value);
      return acc;
    }, {} as any);
  }

  return data;
}
