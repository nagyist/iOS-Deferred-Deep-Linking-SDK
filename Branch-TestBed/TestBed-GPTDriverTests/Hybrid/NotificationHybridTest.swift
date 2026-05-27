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

        // Give it a tiny bit of time to trigger the system animation
        wait(timeout: 0.5)

        // AI: Tap the notification.
        // We prioritize tapping the banner while it's still visible.
        // If it's gone, we ask the AI to pull down the notification shade.
        try driver.execute(
            "A notification banner titled 'Branch Test Notification' is appearing at the top of the screen. " +
                "Tap it immediately. If the banner has already disappeared, pull down the notification shade " +
                "from the top of the screen, find the 'Branch Test Notification', and tap it."
        )

        // Give it time to handle the deep link and push the view
        let logNav = app.navigationBars["Logs"]
        XCTAssertTrue(
            logNav.waitForExistence(timeout: 15),
            "Tapping the notification should have triggered a deep link and pushed the Logs screen"
        )

        // AI VALIDATION: Verify the content of the logs
        try driver.assert(
            "The screen shows Branch deep link metadata (JSON-like text) containing " +
                "keys such as '~channel' or '~feature'"
        )

        // Cleanup
        if logNav.exists {
            let backButton = app.navigationBars.buttons.element(boundBy: 0)
            if backButton.exists { backButton.tap() }
        }
    }
}
