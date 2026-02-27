package calculator;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import static org.junit.jupiter.api.Assertions.*;

class HistoryLoggerTest {

    private HistoryLogger logger;

    @BeforeEach
    void setUp() {
        logger = new HistoryLogger();
    }

    @Test
    void testLog() {
        logger.log("Add", 5);
        assertEquals(1, logger.getHistory().size());
        assertEquals("Add: 5", logger.getHistory().get(0));
    }

    @Test
    void testMultipleLogs() {
        logger.log("Add", 5);
        logger.log("Sub", 3);
        logger.log("Mul", 10);
        
        assertEquals(3, logger.getHistory().size());
        assertEquals("Add: 5", logger.getHistory().get(0));
        assertEquals("Sub: 3", logger.getHistory().get(1));
        assertEquals("Mul: 10", logger.getHistory().get(2));
    }

    @Test
    void testClear() {
        logger.log("Add", 5);
        logger.log("Sub", 3);
        
        logger.clear();
        
        assertTrue(logger.getHistory().isEmpty());
    }

    @Test
    void testGetHistoryReturnsCopy() {
        logger.log("Add", 5);
        
        logger.getHistory().add("Invalid");
        
        assertEquals(1, logger.getHistory().size());
    }
}
