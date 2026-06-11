# Teraz ERP — Session Summary

## Timeline

### Earlier sessions
- Fixed stale `__pycache__` (restart fixed sales order date issue)
- Added `warehouses.delete` + `branches.delete` permissions to GM/WM roles
- Replaced all `'Sales Rep'` frontend role checks with correct `'Sales Officer'`, `'Sales Manager'`, etc.
- Replaced all backend `'Manager'` / `'Warehouse Staff'` with real role names across 6 route files
- Changed `create_adjustment` to `@permission_required('inventory.adjust')` (was unused)
- Fixed all frontend/backend permission mismatches (Accountant from invoices/create, etc.)
- Added `@audit_log` to 44 mutation route functions across 10 files; fixed login audit logging
- Fixed ReportsPage to handle each report type's unique response shape; added CSV export
- Fixed `create_invoice` date parsing; fixed InvoiceFormPage error catch key

### This session
- **Invoice tax auto-populate** — added `Number()` conversion + fallback to `sub + tax`
- **Payment date bug** — `pay_invoice` was passing string to SQLite Date field (same `date.fromisoformat` fix as invoice)
- **Movement type labels** — ledger now shows "Production", "Transfer In", "Transfer Out", "Sales Issue", etc. based on `movement_type` + `reference_type`
- **Backend `reference_type` propagation** — ledger entries now receive the original voucher `reference_type` (Transfer, ProductionBatch, LoadingAuthorization) instead of hardcoded 'GIV'/'GRV'. Fixed in `warehouses/routes.py:approve_grv/giv` and `inventory_service.py:process_goods_issue/receipt`
- **Movement type filter dropdown** — now shows readable labels ("Stock Receipt", "Stock Issue", "Goods Received", "Goods Issued")
- **Error handling review** — found and fixed:
  - Transfer orphaned-GIV/GRV bug: service call wrapped in try/except, orphaned voucher deleted on failure
  - `update_quotation` data-loss: build new items in memory before deleting old ones
  - No logging anywhere: `app.logger.error()` added to 500 handler (traceback), `app.logger.warning()` to JWT callbacks in app.py and decorators.py
  - `audit_log` silent failure: now logs error instead of just `except: pass`
  - `date.fromisoformat` in `create_invoice`: wrapped in try/except, returns 400 with clear message
  - `int(get_jwt_identity())` crash: None-check before `int()` in `get_current_user()` and `auth/routes.py:refresh`
  - `company/routes.py:110` broad `except Exception`: now logs traceback and restores DB file on failed restore
  - Dead `jwt_required` wrapper removed from `decorators.py` (was unused)
- **Quotation form error catch** — reads `data.error` instead of `data.detail` (same fix as invoice form)

## Open issues (not blocking)
- No `try/except` around ~50 `db.session.commit()` calls in routes (500 handler logs traceback now, so acceptable)
- `BaseRepository.create/update` calls `db.session.commit()` inline (design issue, would need layer refactor)
- `audit_log` absorbs audit failures silently (logging added; re-raising would break successful API calls)
