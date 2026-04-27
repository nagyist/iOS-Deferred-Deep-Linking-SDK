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
        Thread.sleep(forTimeInterval: 2)

        // AI: Tap the notification. We'll ask the AI to find it wherever it is.
        // It's most reliable to just ask the AI to handle the notification flow.
        try driver.execute(
            "A local notification titled 'Branch Test Notification' should appear shortly. " +
                "If you see it as a banner, tap it. If not, swipe down from the top to find it in the " +
                "Notification Center and tap it there. This should open the Branch TestBed app."
        )

        // Give it time to handle the deep link and push the view
        Thread.sleep(forTimeInterval: 10)

        // DETERMINISTIC CHECK: Did we reach the Logs screen?
        let logNav = app.navigationBars["Logs"]
        XCTAssertTrue(
            logNav.waitForExistence(timeout: 10),
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
