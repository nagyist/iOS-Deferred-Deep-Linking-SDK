//
//  PluginNotifyHybridTest.swift
//  TestBed-GPTDriverTests
//
//  HYBRID — Tests the `Branch.notifyNativeToInit()` plugin entry
//  point used by React Native / Flutter wrappers to signal that
//  the native SDK should complete its initialization.
//
//  The iOS TestBed does NOT currently ship with a "Simulate Plugin
//  Notify Init" button wired to `Branch.notifyNativeToInit()`.
//  This test is a placeholder skipped at runtime until the TestBed
//  exposes such a button.
//
//  To enable this test:
//    1. Add a "Simulate Plugin Notify Init" button to the Branch
//       TestBed main screen, wired to an IBAction that calls
//       `[[Branch getInstance] notifyNativeToInit]`.
//    2. Add an accessibility identifier (e.g.
//       btn_plugin_notify_init) to that button in
//       TestBedIdentifiers.h/.m and Main.storyboard.
//    3. Remove the XCTSkip below and implement the real flow:
//       tap the button, wait for the init callback, then verify
//       the SDK is still functional by generating a Branch link.
//

import gptd_swift
import XCTest

final class PluginNotifyHybridTest: BaseGptDriverTest {
    func testPluginNotifyInit_sdkRemainsFunctional() throws {
        throw XCTSkip(
            "iOS Branch TestBed does not yet expose a 'Simulate Plugin Notify " +
                "Init' button wired to Branch.notifyNativeToInit(). See the " +
                "header comment of this file for the changes required on the " +
                "TestBed side to enable this test."
        )
    }
}
