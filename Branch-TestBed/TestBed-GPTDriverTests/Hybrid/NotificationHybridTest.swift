//
//  NotificationHybridTest.swift
//  TestBed-GPTDriverTests
//
//  HYBRID — Tests push / local notification delivery carrying a
//  Branch deep link.
//

import gptd_swift
import XCTest

final class NotificationHybridTest: BaseGptDriverTest {
    func testSendNotification_createsNotificationWithBranchLink() throws {
        let button = app.buttons[kTestBedBtnNotificationSend]
        TestScrollHelpers.scrollUntilVisible(button, in: app)
        button.tap()

        // Give it time to schedule
        let expectation = XCTestExpectation(description: "Wait for notification to be scheduled")
        XCTWaiter().wait(for: [expectation], timeout: 2.0)

        // AI: Tap the notification. We'll ask the AI to find it wherever it is.
        // It's most reliable to just ask the AI to handle the notification flow.
        try driver.execute(
            "A local notification titled 'Branch Test Notification' should appear. " +
                "If you see it as a banner, tap it immediately. If it's already gone, " +
                "open the Notification Center (swipe down from the very top edge of the screen) " +
                "and find the notification there to tap it. This should open the Branch TestBed app."
        )

        // Give it time to handle the deep link and push the view
        let logNav = app.navigationBars["Logs"]
        XCTAssertTrue(
            logNav.waitForExistence(timeout: 15),
            "Tapping the notification should have triggered a deep link and pushed the Logs screen"
        )

        // AI VALIDATION: Verify the content of the logs
        try driver.assert(
            "The screen shows Branch deep link metadata (JSON-like text) containing keys such as '~channel' or '~feature'"
        )

        // Cleanup
        if logNav.exists {
            let backButton = app.navigationBars.buttons.element(boundBy: 0)
            if backButton.exists { backButton.tap() }
        }
    }
}
