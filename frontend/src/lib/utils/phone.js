import { isValidPhoneNumber, parsePhoneNumber, isPossiblePhoneNumber } from 'libphonenumber-js';

/**
 * Validates a phone number and returns validation result
 * @param {string} phoneNumber - The phone number to validate
 * @param {string} [defaultCountry] - Default country code (e.g., 'US', 'IN')
 * @returns {{ isValid: boolean, formatted?: string, error?: string }}
 */
export function validatePhoneNumber(phoneNumber, defaultCountry) {
  if (!phoneNumber || phoneNumber.trim() === '') {
    return { isValid: true }; // Allow empty phone numbers
  }

  const trimmed = phoneNumber.trim();

  try {
    // If the number starts with +, validate as international
    if (trimmed.startsWith('+')) {
      const isValid = isValidPhoneNumber(trimmed);
      if (!isValid) {
        return {
          isValid: false,
          error: 'Please enter a valid phone number with country code'
        };
      }
      const parsed = parsePhoneNumber(trimmed);
      return {
        isValid: true,
        formatted: parsed.formatInternational()
      };
    }

    // For numbers without country code, try with default country if provided
    if (defaultCountry) {
      // @ts-ignore - defaultCountry is a valid CountryCode
      const isValid = isValidPhoneNumber(trimmed, defaultCountry);
      if (isValid) {
        // @ts-ignore
        const parsed = parsePhoneNumber(trimmed, defaultCountry);
        return {
          isValid: true,
          formatted: parsed.formatInternational()
        };
      }
    }

    // Try common countries for numbers without + prefix
    const commonCountries = ['IN', 'US', 'GB', 'AU', 'CA', 'DE', 'FR'];
    for (const country of commonCountries) {
      try {
        // @ts-ignore
        if (isValidPhoneNumber(trimmed, country)) {
          // @ts-ignore
          const parsed = parsePhoneNumber(trimmed, country);
          return {
            isValid: true,
            formatted: parsed.formatInternational()
          };
        }
      } catch {
        continue;
      }
    }

    // If nothing worked, check if it's at least a possible phone number
    // (has right length, starts with valid digits, etc.)
    if (isPossiblePhoneNumber(trimmed, 'IN') || isPossiblePhoneNumber(trimmed, 'US')) {
      return {
        isValid: true,
        formatted: trimmed
      };
    }

    return {
      isValid: false,
      error:
        'Please enter a valid phone number (include country code like +91 for India or +1 for US)'
    };
  } catch (error) {
    return {
      isValid: false,
      error: 'Please enter a valid phone number'
    };
  }
}

/**
 * Formats a phone number for display
 * @param {string} phoneNumber - The phone number to format
 * @param {string} defaultCountry - Default country code
 * @returns {string} Formatted phone number or original if invalid
 */
export function formatPhoneNumber(phoneNumber, defaultCountry = 'US') {
  if (!phoneNumber) return '';

  try {
    // @ts-ignore - defaultCountry is a valid CountryCode
    const parsed = parsePhoneNumber(phoneNumber, { defaultCountry });
    return parsed.formatInternational();
  } catch {
    return phoneNumber; // Return original if parsing fails
  }
}

/**
 * Formats a phone number for storage (E.164 format)
 * @param {string} phoneNumber - The phone number to format
 * @param {string} [defaultCountry] - Default country code
 * @returns {string} E.164 formatted phone number or original if invalid
 */
export function formatPhoneForStorage(phoneNumber, defaultCountry) {
  if (!phoneNumber) return '';

  const trimmed = phoneNumber.trim();

  try {
    // If starts with +, parse as international
    if (trimmed.startsWith('+')) {
      const parsed = parsePhoneNumber(trimmed);
      return parsed.format('E.164');
    }

    // Try with default country first
    if (defaultCountry) {
      try {
        // @ts-ignore
        const parsed = parsePhoneNumber(trimmed, defaultCountry);
        if (parsed.isValid()) {
          return parsed.format('E.164');
        }
      } catch {
        // Continue to try other countries
      }
    }

    // Try common countries
    const commonCountries = ['IN', 'US', 'GB', 'AU', 'CA', 'DE', 'FR'];
    for (const country of commonCountries) {
      try {
        // @ts-ignore
        const parsed = parsePhoneNumber(trimmed, country);
        if (parsed.isValid()) {
          return parsed.format('E.164');
        }
      } catch {
        continue;
      }
    }

    return phoneNumber; // Return original if parsing fails
  } catch {
    return phoneNumber; // Return original if parsing fails
  }
}
