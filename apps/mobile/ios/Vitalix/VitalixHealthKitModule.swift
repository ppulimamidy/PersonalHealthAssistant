import ExpoModulesCore
import HealthKit

/// Custom Expo Module wrapping HealthKit with ObjC @try/@catch safety.
/// EXUtilities.catchException converts NSExceptions → Swift errors BEFORE they
/// reach any async machinery, avoiding the EXC_BREAKPOINT / completeTaskWithClosure
/// crash that Nitro Modules causes when HealthKit throws without an entitlement.
public class VitalixHealthKitModule: Module {
  private let store = HKHealthStore()

  public func definition() -> ModuleDefinition {
    Name("VitalixHealthKit")

    // MARK: - requestAuthorization
    AsyncFunction("requestAuthorization") { (promise: Promise) in
      guard HKHealthStore.isHealthDataAvailable() else {
        promise.reject("UNAVAILABLE", "HealthKit is not available on this device or simulator.")
        return
      }

      let typesToRead: Set<HKObjectType> = [
        HKObjectType.quantityType(forIdentifier: .stepCount)!,
        HKObjectType.quantityType(forIdentifier: .heartRate)!,
        HKObjectType.quantityType(forIdentifier: .heartRateVariabilitySDNN)!,
        HKObjectType.quantityType(forIdentifier: .oxygenSaturation)!,
        HKObjectType.categoryType(forIdentifier: .sleepAnalysis)!,
      ]

      // EXUtilities.catchException is bridged to Swift as 'throws' — catches NSException
      do {
        try EXUtilities.catchException {
          self.store.requestAuthorization(toShare: [], read: typesToRead) { _, error in
            if let error = error {
              promise.reject(error)
            } else {
              promise.resolve(true)
            }
          }
        }
      } catch {
        promise.reject(error)
      }
    }

    // MARK: - queryQuantitySamples
    // Returns [{startDate: ms, endDate: ms, quantity: Double}]
    AsyncFunction("queryQuantitySamples") { (identifier: String, fromMs: Double, toMs: Double, promise: Promise) in
      let qid = HKQuantityTypeIdentifier(rawValue: identifier)
      guard let qtype = HKObjectType.quantityType(forIdentifier: qid) else {
        promise.reject("INVALID_TYPE", "Unknown quantity type: \(identifier)")
        return
      }

      let from = Date(timeIntervalSince1970: fromMs / 1000.0)
      let to   = Date(timeIntervalSince1970: toMs   / 1000.0)
      let pred = HKQuery.predicateForSamples(withStart: from, end: to, options: .strictStartDate)
      let unit = self.unitFor(identifier: identifier)

      let query = HKSampleQuery(
        sampleType: qtype, predicate: pred,
        limit: HKObjectQueryNoLimit, sortDescriptors: nil
      ) { _, samples, error in
        if let error = error { promise.reject(error); return }
        let result: [[String: Any]] = (samples ?? []).compactMap { s in
          guard let q = s as? HKQuantitySample else { return nil }
          return [
            "startDate": q.startDate.timeIntervalSince1970 * 1000.0,
            "endDate":   q.endDate.timeIntervalSince1970   * 1000.0,
            "quantity":  q.quantity.doubleValue(for: unit),
          ]
        }
        promise.resolve(result)
      }

      do {
        try EXUtilities.catchException { self.store.execute(query) }
      } catch {
        promise.reject(error)
      }
    }

    // MARK: - queryCategorySamples
    // Returns [{startDate: ms, endDate: ms, value: Int}]
    AsyncFunction("queryCategorySamples") { (identifier: String, fromMs: Double, toMs: Double, promise: Promise) in
      let cid = HKCategoryTypeIdentifier(rawValue: identifier)
      guard let ctype = HKObjectType.categoryType(forIdentifier: cid) else {
        promise.reject("INVALID_TYPE", "Unknown category type: \(identifier)")
        return
      }

      let from = Date(timeIntervalSince1970: fromMs / 1000.0)
      let to   = Date(timeIntervalSince1970: toMs   / 1000.0)
      let pred = HKQuery.predicateForSamples(withStart: from, end: to, options: .strictStartDate)

      let query = HKSampleQuery(
        sampleType: ctype, predicate: pred,
        limit: HKObjectQueryNoLimit, sortDescriptors: nil
      ) { _, samples, error in
        if let error = error { promise.reject(error); return }
        let result: [[String: Any]] = (samples ?? []).compactMap { s in
          guard let c = s as? HKCategorySample else { return nil }
          return [
            "startDate": c.startDate.timeIntervalSince1970 * 1000.0,
            "endDate":   c.endDate.timeIntervalSince1970   * 1000.0,
            "value":     c.value,
          ]
        }
        promise.resolve(result)
      }

      do {
        try EXUtilities.catchException { self.store.execute(query) }
      } catch {
        promise.reject(error)
      }
    }
  }

  private func unitFor(identifier: String) -> HKUnit {
    switch identifier {
    case HKQuantityTypeIdentifier.heartRate.rawValue:
      return HKUnit.count().unitDivided(by: .minute())
    case HKQuantityTypeIdentifier.heartRateVariabilitySDNN.rawValue:
      return HKUnit.secondUnit(with: .milli)
    case HKQuantityTypeIdentifier.oxygenSaturation.rawValue:
      return .percent()
    default:
      return .count()  // steps
    }
  }
}
