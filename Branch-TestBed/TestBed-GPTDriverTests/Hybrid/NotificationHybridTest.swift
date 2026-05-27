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

        // 1. DETERMINISTIC STEP:
        // Target the iOS SpringBoard to catch the banner BEFORE XCUITest's
        // interruption monitor forces a wait for it to disappear.
        let springboard = XCUIApplication(bundleIdentifier: "com.apple.springboard")

        // Try multiple banner identifiers / label matchers — exact accessibility id
        // varies between iOS versions. On iOS 18.4 the banner may not register as
        // "NotificationShortLookView"; fall back to a label-contains query.
        let bannerPredicate = NSPredicate(
            format: "identifier == 'NotificationShortLookView' OR identifier == 'NotificationCell' " +
                "OR label CONTAINS[c] 'Branch Test Notification'"
        )
        let banner = springboard.descendants(matching: .any).matching(bannerPredicate).firstMatch

        var tapped = false
        if banner.waitForExistence(timeout: 15) {
            // Coordinate-based center tap — more robust than .tap() because
            // notification banners sometimes have non-tappable edges.
            banner.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)).tap()
            tapped = true
        }

        if !tapped {
            // 2. AI FALLBACK:
            // If the deterministic tap missed the banner, use AI to open
            // Notification Center and tap the notification by title.
            try driver.execute(
                """
                Slide down 60% from the system time on top of the screen.
                This should open Notification Center.
                Then find the notification titled "Branch Test Notification" and tap it.
                """
            )
        }

        // Give it time to handle the deep link and push the view
        let logNav = app.navigationBars["Logs"]
        XCTAssertTrue(logNav.waitForExistence(timeout: 15),
                      "Tapping the notification should have triggered a deep link and pushed the Logs screen")

        // AI VALIDATION: Verify the content of the logs
        // The Logs screen renders "Successfully Deeplinked:\n\n<text>\nSession Details:\n\n<dict>"
        // where <dict> includes Branch link parameters. Accept any one of several
        // markers to keep this resilient across SDK versions / link payloads.
        try driver.assert(
            "The screen contains Branch session or deep-link information. " +
                "Look for ANY of these markers: 'Successfully Deeplinked', " +
                "'Session Details', '+clicked_branch_link', '~channel', '~feature', " +
                "'~campaign', '+match_guaranteed', or a JSON/dictionary-like block " +
                "with key=value pairs."
        )

        // Cleanup
        if logNav.exists {
            let backButton = app.navigationBars.buttons.element(boundBy: 0)
            if backButton.exists { backButton.tap() }
        }
    }
}
