import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_client.dart';
import '../theme.dart';

class AccountsScreen extends StatefulWidget {
  const AccountsScreen({super.key});

  @override
  State<AccountsScreen> createState() => _AccountsScreenState();
}

class _AccountsScreenState extends State<AccountsScreen> {
  final _formKey = GlobalKey<FormState>();
  String _login = '';
  String _password = '';
  String _server = '';
  String _broker = 'MetaQuotes';
  
  List<dynamic> _accounts = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _fetchAccounts();
  }

  Future<void> _fetchAccounts() async {
    setState(() => _loading = true);
    try {
      final api = context.read<ApiClient>();
      final data = await api.get('/api/v1/accounts');
      setState(() => _accounts = (data as Map<String, dynamic>)['accounts'] as List);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red));
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _addAccount() async {
    if (!_formKey.currentState!.validate()) return;
    try {
      final api = context.read<ApiClient>();
      await api.post('/api/v1/accounts', body: {
        'login': int.parse(_login),
        'password': _password,
        'server': _server,
        'broker': _broker,
      });
      _fetchAccounts();
      _formKey.currentState!.reset();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Account secured in vault'), backgroundColor: Colors.green));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed: $e'), backgroundColor: Colors.red));
      }
    }
  }

  Future<void> _deleteAccount(int id) async {
    try {
      final api = context.read<ApiClient>();
      await api.delete('/api/v1/accounts/$id');
      _fetchAccounts();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: VeloraTheme.backgroundColor,
      appBar: AppBar(
        title: const Text('MT5 Accounts', style: TextStyle(fontWeight: FontWeight.w800)),
        backgroundColor: VeloraTheme.surfaceColor,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            _buildAddCard(),
            const SizedBox(height: 16),
            _buildVaultCard(),
          ],
        ),
      ),
    );
  }

  Widget _buildAddCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: VeloraTheme.surfaceColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.white.withOpacity(0.07)),
      ),
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Add MT5 Vault', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
            const SizedBox(height: 16),
            TextFormField(
              keyboardType: TextInputType.number,
              style: const TextStyle(color: Colors.white),
              decoration: _inputDecoration('Login ID'),
              onChanged: (v) => _login = v,
              validator: (v) => v!.isEmpty ? 'Required' : null,
            ),
            const SizedBox(height: 10),
            TextFormField(
              obscureText: true,
              style: const TextStyle(color: Colors.white),
              decoration: _inputDecoration('Password'),
              onChanged: (v) => _password = v,
              validator: (v) => v!.isEmpty ? 'Required' : null,
            ),
            const SizedBox(height: 10),
            TextFormField(
              style: const TextStyle(color: Colors.white),
              decoration: _inputDecoration('Server (e.g. MetaQuotes-Demo)'),
              onChanged: (v) => _server = v,
              validator: (v) => v!.isEmpty ? 'Required' : null,
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _addAccount,
                style: ElevatedButton.styleFrom(
                  backgroundColor: VeloraTheme.primaryColor,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
                child: const Text('ENCRYPT & SAVE', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.black)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildVaultCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: VeloraTheme.surfaceColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.white.withOpacity(0.07)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Active Vaults', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
              const Icon(Icons.lock, color: Colors.green, size: 16),
            ],
          ),
          const SizedBox(height: 16),
          if (_loading) 
            const Center(child: CircularProgressIndicator())
          else if (_accounts.isEmpty)
            const Text('No accounts in vault.', style: TextStyle(color: Colors.white38, fontSize: 12))
          else
            ..._accounts.map((acc) => _accountRow(acc)),
        ],
      ),
    );
  }

  Widget _accountRow(dynamic acc) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.03),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        children: [
          const CircleAvatar(backgroundColor: Colors.white10, child: Icon(Icons.account_balance, color: Colors.white70, size: 16)),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('${acc['broker']} — ${acc['login']}', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
                Text(acc['server'], style: const TextStyle(color: Colors.white38, fontSize: 11)),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.delete_outline, color: Colors.redAccent, size: 20),
            onPressed: () => _deleteAccount(acc['id']),
          ),
        ],
      ),
    );
  }

  InputDecoration _inputDecoration(String hint) => InputDecoration(
    hintText: hint,
    hintStyle: const TextStyle(color: Colors.white24, fontSize: 13),
    filled: true,
    fillColor: Colors.white.withOpacity(0.03),
    border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
  );
}
