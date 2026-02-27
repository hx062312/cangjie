package calculator;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class ValidatorTest {

    @Test
    void testValidValues() {
        assertTrue(Validator.isValid(0));
        assertTrue(Validator.isValid(1));
        assertTrue(Validator.isValid(500));
        assertTrue(Validator.isValid(999));
    }

    @Test
    void testInvalidValues() {
        assertFalse(Validator.isValid(-1));
        assertFalse(Validator.isValid(1000));
        assertFalse(Validator.isValid(-100));
        assertFalse(Validator.isValid(2000));
    }
}
