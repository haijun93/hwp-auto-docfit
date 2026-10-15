/// Save acknowledgements cover only the generation present in that snapshot.
class EditSaveState {
  int generation = 0, savedGeneration = 0, pending = 0;
  bool get dirty => generation > savedGeneration;
  bool get saving => pending > 0;
  void event(Object? rawGeneration, bool dirty) {
    final value = rawGeneration is int ? rawGeneration : generation + 1;
    if (value < generation) return;
    generation = value;
    if (!dirty) savedGeneration = value;
  }

  int begin(Object? rawGeneration) {
    pending++;
    return rawGeneration is int ? rawGeneration : generation;
  }

  void complete(int target, {required bool success}) {
    if (pending > 0) pending--;
    if (success && target > savedGeneration) savedGeneration = target;
  }
}
