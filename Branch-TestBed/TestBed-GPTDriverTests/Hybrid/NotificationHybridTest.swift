//
//  NotificationHybridTest.swift
//  TestBed-GPTDriverTests
//
//  HYBRID — Tests push / local notification delivery carrying a
//  Branch deep link.
//
//  The iOS TestBed does NOT currently ship with a "Send
//  Notification" button that generates a Branch link and posts a
//  local notification. This test is a placeholder skipped at
//  runtime until the TestBed exposes such a flow.
//
//  To enable this test:
//    1. Add a "Send Notification" button to the Branch TestBed
//       main screen, wired to an IBAction that:
//         - Generates a Branch short link via Branch.getShortURL
//         - Schedules a local UNNotificationRequest with that URL
//           embedded in `userInfo` so tapping it triggers
//           Branch.handleUniversalDeepLink.
//    2. Add an accessibility identifier (e.g. btn_send_notification)
//       to that button in TestBedIdentifiers.h/.m and
//       Main.storyboard.
//    3. Remove the XCTSkip below and implement the real flow:
//       tap the button, wait for the notification, swipe down from
//       the top of the screen to reveal Notification Center, tap
//       the BranchTest notification, assert on the arrival of
//       deep link params.
//

import gptd_swift
import XCTest

final class NotificationHybridTest: BaseGptDriverTest {
    func testSendNotification_createsNotificationWithBranchLink() throws {
        throw XCTSkip(
            "iOS Branch TestBed does not yet expose a 'Send Notification' " +
                "button. See the header comment of this file for the changes " +
                "required on the TestBed side to enable this test."
        )
    }
}
