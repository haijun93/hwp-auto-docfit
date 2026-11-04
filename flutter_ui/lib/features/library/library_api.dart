enum LibrarySpace { core, basis, reference, temp }

enum LibraryItemKind {
  file,
  folder,
  link,
  text,
  richText,
  image,
  capture,
  note,
}

class LibraryBox {
  const LibraryBox({required this.id, required this.name});
  final String id;
  final String name;
}

class LibraryItem {
  const LibraryItem({
    required this.id,
    required this.boxId,
    required this.kind,
    required this.title,
    required this.space,
    required this.x,
    required this.y,
    this.source,
    this.text,
  });

  final String id;
  final String boxId;
  final LibraryItemKind kind;
  final String title;
  final LibrarySpace space;
  final double x;
  final double y;
  final String? source; // 파일 경로 또는 URL 참조. 파일 원본의 복사/이동 금지.
  final String? text; // 사용자 입력 텍스트 자료 내용.

  LibraryItem copyWith({
    String? id,
    String? boxId,
    LibraryItemKind? kind,
    String? title,
    LibrarySpace? space,
    double? x,
    double? y,
    String? source,
    String? text,
  }) {
    return LibraryItem(
      id: id ?? this.id,
      boxId: boxId ?? this.boxId,
      kind: kind ?? this.kind,
      title: title ?? this.title,
      space: space ?? this.space,
      x: x ?? this.x,
      y: y ?? this.y,
      source: source ?? this.source,
      text: text ?? this.text,
    );
  }
}

class LibraryRelation {
  const LibraryRelation({
    required this.id,
    required this.boxId,
    required this.fromItemId,
    required this.toItemId,
    this.label,
  });

  final String id;
  final String boxId;
  final String fromItemId;
  final String toItemId;
  final String? label;
}

abstract interface class LibraryApi {
  /// klib 요청: library_list_boxes
  /// 인자: 없음
  Future<List<LibraryBox>> listBoxes();

  /// klib 요청: library_create_box
  /// 인자: name
  Future<LibraryBox> createBox(String name);

  /// klib 요청: library_list_items
  /// 인자: box_id, query
  Future<List<LibraryItem>> listItems(String boxId, {String query = ''});

  /// klib 요청: library_add_item
  /// 인자: box_id, kind, title, space, x, y, source?, text?
  Future<LibraryItem> addItem({
    required String boxId,
    required LibraryItemKind kind,
    required String title,
    required LibrarySpace space,
    required double x,
    required double y,
    String? source,
    String? text,
  });

  /// klib 요청: library_move_item
  /// 인자: item_id, space, x, y
  Future<LibraryItem> moveItem(
    String itemId, {
    required String boxId,
    required LibrarySpace space,
    required double x,
    required double y,
  });

  /// klib 요청: library_list_relations
  /// 인자: box_id
  Future<List<LibraryRelation>> listRelations(String boxId);

  /// klib 요청: library_add_relation
  /// 인자: box_id, from_item_id, to_item_id
  Future<LibraryRelation> addRelation(
    String boxId,
    String fromItemId,
    String toItemId,
  );

  /// klib 요청: library_delete_relation
  /// 인자: relation_id
  Future<void> deleteRelation(String relationId);
}

class InMemoryLibraryApi implements LibraryApi {
  InMemoryLibraryApi({
    List<LibraryBox>? initialBoxes,
    List<LibraryItem>? initialItems,
    List<LibraryRelation>? initialRelations,
  }) {
    if (initialBoxes != null) {
      for (final box in initialBoxes) {
        _boxes[box.id] = box;
        _boxSequence = _maxSequence(_boxSequence, box.id, 'box_');
      }
    }
    if (initialItems != null) {
      for (final item in initialItems) {
        _items[item.id] = item;
        _itemSequence = _maxSequence(_itemSequence, item.id, 'item_');
      }
    }
    if (initialRelations != null) {
      for (final relation in initialRelations) {
        _relations[relation.id] = relation;
        _relationSequence = _maxSequence(_relationSequence, relation.id, 'rel_');
      }
    }
  }

  final Map<String, LibraryBox> _boxes = <String, LibraryBox>{};
  final Map<String, LibraryItem> _items = <String, LibraryItem>{};
  final Map<String, LibraryRelation> _relations = <String, LibraryRelation>{};

  int _boxSequence = 0;
  int _itemSequence = 0;
  int _relationSequence = 0;

  int _maxSequence(int current, String id, String prefix) {
    if (!id.startsWith(prefix)) return current;
    final suffix = int.tryParse(id.substring(prefix.length));
    return suffix == null || suffix < current ? current : suffix;
  }

  @override
  Future<List<LibraryBox>> listBoxes() async {
    return _boxes.values.toList(growable: false);
  }

  @override
  Future<LibraryBox> createBox(String name) async {
    final trimmed = name.trim();
    if (trimmed.isEmpty) {
      throw ArgumentError('자료함 이름은 비어 있을 수 없습니다.');
    }
    _boxSequence++;
    final id = 'box_$_boxSequence';
    final box = LibraryBox(id: id, name: trimmed);
    _boxes[id] = box;
    return box;
  }

  @override
  Future<List<LibraryItem>> listItems(String boxId, {String query = ''}) async {
    final trimmedQuery = query.trim().toLowerCase();
    final itemsInBox = _items.values.where((item) => item.boxId == boxId);
    if (trimmedQuery.isEmpty) {
      return itemsInBox.toList(growable: false);
    }
    return itemsInBox.where((item) {
      final titleMatch = item.title.toLowerCase().contains(trimmedQuery);
      final textMatch = item.text?.toLowerCase().contains(trimmedQuery) ?? false;
      return titleMatch || textMatch;
    }).toList(growable: false);
  }

  @override
  Future<LibraryItem> addItem({
    required String boxId,
    required LibraryItemKind kind,
    required String title,
    required LibrarySpace space,
    required double x,
    required double y,
    String? source,
    String? text,
  }) async {
    if (!_boxes.containsKey(boxId)) {
      throw StateError('자료함이 존재하지 않습니다: $boxId');
    }
    _itemSequence++;
    final id = 'item_$_itemSequence';
    final item = LibraryItem(
      id: id,
      boxId: boxId,
      kind: kind,
      title: title,
      space: space,
      x: x,
      y: y,
      source: source,
      text: text,
    );
    _items[id] = item;
    return item;
  }

  @override
  Future<LibraryItem> moveItem(
    String itemId, {
    required String boxId,
    required LibrarySpace space,
    required double x,
    required double y,
  }) async {
    final existing = _items[itemId];
    if (existing == null) {
      throw StateError('항목이 존재하지 않습니다: $itemId');
    }
    if (!_boxes.containsKey(existing.boxId)) {
      throw StateError('항목이 속한 자료함이 존재하지 않습니다: ${existing.boxId}');
    }
    if (existing.boxId != boxId) {
      throw StateError('항목이 요청한 자료함에 속하지 않습니다: $boxId');
    }
    final updated = existing.copyWith(space: space, x: x, y: y);
    _items[itemId] = updated;
    return updated;
  }

  @override
  Future<List<LibraryRelation>> listRelations(String boxId) async {
    return _relations.values
        .where((relation) => relation.boxId == boxId)
        .toList(growable: false);
  }

  @override
  Future<LibraryRelation> addRelation(
    String boxId,
    String fromItemId,
    String toItemId,
  ) async {
    if (fromItemId == toItemId) {
      throw ArgumentError('자료는 자기 자신과 관계를 맺을 수 없습니다.');
    }
    final fromItem = _items[fromItemId];
    final toItem = _items[toItemId];
    if (fromItem == null || toItem == null) {
      throw StateError('연결할 항목을 찾을 수 없습니다.');
    }
    if (fromItem.boxId != boxId || toItem.boxId != boxId) {
      throw StateError('다른 자료함의 항목과는 관계를 맺을 수 없습니다.');
    }
    if (fromItem.space != LibrarySpace.core ||
        toItem.space != LibrarySpace.core) {
      throw ArgumentError('관계선은 핵심자료 공간의 자료 사이에만 생성할 수 있습니다.');
    }

    final duplicate = _relations.values.any(
      (rel) =>
          rel.boxId == boxId &&
          ((rel.fromItemId == fromItemId && rel.toItemId == toItemId) ||
              (rel.fromItemId == toItemId && rel.toItemId == fromItemId)),
    );
    if (duplicate) {
      throw StateError('이미 두 자료 사이에 관계가 존재합니다.');
    }

    _relationSequence++;
    final id = 'rel_$_relationSequence';
    final relation = LibraryRelation(
      id: id,
      boxId: boxId,
      fromItemId: fromItemId,
      toItemId: toItemId,
    );
    _relations[id] = relation;
    return relation;
  }

  @override
  Future<void> deleteRelation(String relationId) async {
    _relations.remove(relationId);
  }
}
